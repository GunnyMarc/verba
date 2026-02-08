from pathlib import Path

from .base import make_progress_callback, suppress_stdout


class AudiotrAdapter:

    @staticmethod
    def run(job, upload_path: str, output_dir: str, settings: dict) -> dict:
        job.start()
        callback = make_progress_callback(job)
        try:
            from audiotr.src.pipeline import TranscriptionPipeline

            pipeline = TranscriptionPipeline(
                model_size=settings.get("whisper_model", "base"),
                language=settings.get("language", "auto"),
                device=settings.get("device", "auto"),
                markdown_style=settings.get("markdown_style", "timestamped"),
                include_metadata=settings.get("include_metadata", True),
            )

            input_path = Path(upload_path)
            output_path = Path(output_dir) / f"{input_path.stem}_transcript.md"

            with suppress_stdout():
                result = pipeline.process(
                    str(input_path), str(output_path), callback
                )

            if result.success:
                markdown_content = output_path.read_text(encoding="utf-8") if output_path.exists() else ""
                job.complete({
                    "type": "single",
                    "markdown_content": markdown_content,
                    "output_path": str(output_path),
                    "audio_info": getattr(result, "audio_info", {}),
                    "language": getattr(result, "language", ""),
                    "word_count": getattr(result, "word_count", 0),
                    "segment_count": getattr(result, "segment_count", 0),
                })
            else:
                job.fail(getattr(result, "error", "Transcription failed"))

            try:
                pipeline.cleanup()
            except Exception:
                pass

        except Exception as e:
            job.fail(str(e))

        return job.to_dict()

    @staticmethod
    def run_batch(job, file_paths: list[str], output_dir: str, settings: dict) -> dict:
        job.start()
        total = len(file_paths)
        results = []
        success_count = 0
        failed_count = 0

        for i, file_path in enumerate(file_paths, 1):
            job.update_progress(
                int((i - 1) / total * 100),
                f"Processing {i}/{total}: {Path(file_path).name}",
            )
            try:
                from audiotr.src.pipeline import TranscriptionPipeline

                pipeline = TranscriptionPipeline(
                    model_size=settings.get("whisper_model", "base"),
                    language=settings.get("language", "auto"),
                    device=settings.get("device", "auto"),
                    markdown_style=settings.get("markdown_style", "timestamped"),
                    include_metadata=settings.get("include_metadata", True),
                )

                input_path = Path(file_path)
                output_path = Path(output_dir) / f"{input_path.stem}_transcript.md"

                with suppress_stdout():
                    result = pipeline.process(str(input_path), str(output_path), None)

                if result.success:
                    success_count += 1
                    results.append({"file": input_path.name, "success": True})
                else:
                    failed_count += 1
                    results.append({"file": input_path.name, "success": False, "error": getattr(result, "error", "Failed")})

                try:
                    pipeline.cleanup()
                except Exception:
                    pass

            except Exception as e:
                failed_count += 1
                results.append({"file": Path(file_path).name, "success": False, "error": str(e)})

        job.complete({
            "type": "batch",
            "total": total,
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
        })

        return job.to_dict()
