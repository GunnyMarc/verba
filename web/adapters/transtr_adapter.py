import os
from pathlib import Path

from .base import make_progress_callback


class TranstrAdapter:

    @staticmethod
    def run(job, text: str, instructions: str, settings: dict) -> dict:
        job.start()
        callback = make_progress_callback(job)
        try:
            model = settings.get("model", "llama3:latest")
            base_url = settings.get("ollama_base_url", "http://localhost:11434")

            # Check API key availability for cloud models
            from web.config import is_openai_model, is_google_model

            if is_openai_model(model) and not os.environ.get("OPENAI_API_KEY"):
                job.fail("OpenAI API key is not configured. Please add it in Settings.")
                return job.to_dict()

            if is_google_model(model) and not os.environ.get("GOOGLE_API_KEY"):
                job.fail("Google API key is not configured. Please add it in Settings.")
                return job.to_dict()

            callback(10, "Sending to LLM...")

            from transtr.summarizer import summarize

            summary = summarize(
                text=text,
                instructions=instructions,
                model=model,
                base_url=base_url,
            )

            callback(90, "Finalizing...")

            job.complete({
                "type": "single",
                "summary": summary,
                "model_used": model,
                "input_length": len(text),
                "output_length": len(summary),
            })

        except Exception as e:
            job.fail(str(e))

        return job.to_dict()

    @staticmethod
    def run_batch(job, texts: list[dict], instructions: str, settings: dict) -> dict:
        """texts is a list of dicts: [{"filename": str, "text": str}, ...]"""
        job.start()
        total = len(texts)
        results = []
        success_count = 0
        failed_count = 0

        model = settings.get("model", "llama3:latest")
        base_url = settings.get("ollama_base_url", "http://localhost:11434")

        for i, item in enumerate(texts, 1):
            job.update_progress(
                int((i - 1) / total * 100),
                f"Summarizing {i}/{total}: {item['filename']}",
            )
            try:
                from transtr.summarizer import summarize

                summary = summarize(
                    text=item["text"],
                    instructions=instructions,
                    model=model,
                    base_url=base_url,
                )
                success_count += 1
                results.append({
                    "file": item["filename"],
                    "success": True,
                    "summary": summary,
                })
            except Exception as e:
                failed_count += 1
                results.append({
                    "file": item["filename"],
                    "success": False,
                    "error": str(e),
                })

        job.complete({
            "type": "batch",
            "total": total,
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        })

        return job.to_dict()
