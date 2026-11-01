"""Reviewed presentation-copy overrides for legacy five-minute summaries.

The baseline research notes remain intact. Only explicitly approved prose fields
are replaced, without changing source claims or the original chapter structure.
"""
import json
from pathlib import Path

def effective_summaries(root: Path):
    source=json.loads((root/"data/summaries.json").read_text(encoding="utf-8"))
    changes=json.loads((root/"data/summary_editorial_edits.json").read_text(encoding="utf-8"))
    for video_id, fields in changes.items():
        if video_id not in source:
            raise ValueError(f"Unknown summary ID: {video_id}")
        if set(fields)!={"lead"} or not isinstance(fields["lead"],str):
            raise ValueError(f"Unsupported summary edit: {video_id}")
        source[video_id] = {**source[video_id], **fields}
    return source
