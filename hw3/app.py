from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import gradio as gr

from search import (
    LocalImageSearchIndex,
    SearchResult,
)


INDEX_DIR = Path("index")
FAVORITES_DIR = Path("favorites")
MODEL_NAME = "openai/clip-vit-base-patch32"
SPLIT_NAMES = {"train", "test", "val", "iconic-images-and-descriptions"}

APP_CSS = """
.status-strip {
    border: 1px solid #ececec;
    border-radius: 8px;
    padding: 10px 14px;
    background: #fafafa;
}
.query-panel {
    border: 1px solid #e7e7e7;
    border-radius: 8px;
    padding: 14px;
}
.primary-action button {
    min-height: 46px;
    font-weight: 700;
}
"""

search_index = LocalImageSearchIndex(index_dir=INDEX_DIR, model_name=MODEL_NAME)
index_loaded = False


def ensure_index_loaded() -> None:
    global index_loaded
    if not index_loaded:
        search_index.load()
        index_loaded = True


def serialize_results(results: list[SearchResult]) -> list[dict[str, Any]]:
    return [{"path": result.path, "score": result.score} for result in results]


def deserialize_results(results: list[dict[str, Any]] | None) -> list[SearchResult]:
    if not results:
        return []
    return [
        SearchResult(path=str(item["path"]), score=float(item["score"]))
        for item in results
    ]


def display_name(value: str) -> str:
    return value.replace("_Iconic", "").replace("_", " ").replace("-", " ").strip()


def result_metadata(path_value: str) -> dict[str, str]:
    path = Path(path_value)
    parts = path.parts
    split = "sample"
    group = ""
    coarse = ""
    fine = display_name(path.stem)

    for index, part in enumerate(parts):
        if part in SPLIT_NAMES:
            split = "iconic" if part == "iconic-images-and-descriptions" else part
            directories = parts[index + 1 : -1]
            if directories:
                group = directories[0]
                coarse = directories[1] if len(directories) > 1 else directories[0]
                fine = directories[-1] if len(directories) > 2 else coarse
            break

    if not coarse:
        coarse = group or "Sample"
    if not fine:
        fine = path.parent.name

    category = display_name(fine)
    group_label = display_name(group) if group else "Sample"
    coarse_label = display_name(coarse)
    return {
        "category": category,
        "group": group_label,
        "coarse": coarse_label,
        "split": split,
        "file": path.name,
    }


def filter_results(
    results: list[SearchResult],
    min_score: float,
    only_same_category: bool,
) -> list[SearchResult]:
    filtered = [result for result in results if result.score >= float(min_score)]
    if only_same_category and filtered:
        target = result_metadata(filtered[0].path)["category"]
        filtered = [
            result
            for result in filtered
            if result_metadata(result.path)["category"] == target
        ]
    return filtered


def gallery_items(results: list[SearchResult]) -> list[tuple[str, str]]:
    items = []
    for result in results:
        items.append((result.path, f"score: {result.score:.3f}"))
    return items


def result_table(results: list[SearchResult]) -> list[list[str | float]]:
    return [
        [index + 1, round(result.score, 4)]
        for index, result in enumerate(results)
    ]


def result_choices(results: list[SearchResult]) -> list[str]:
    choices = []
    for index, result in enumerate(results):
        choices.append(f"{index + 1} | score {result.score:.3f}")
    return choices


def selected_index(choice: str | None) -> int | None:
    if not choice:
        return None
    try:
        return int(str(choice).split("|", 1)[0].strip()) - 1
    except ValueError:
        return None


def run_search(
    mode: str,
    text_query: str,
    image_query,
    top_k: int,
    min_score: float,
    only_same_category: bool,
) -> tuple[
    list[tuple[str, str]],
    str,
    list[list[str | float]],
    list[dict[str, Any]],
    Any,
    str | None,
    str,
]:
    try:
        ensure_index_loaded()
        candidate_count = max(int(top_k) * 8, 40)
        if mode == "Text":
            results = search_index.search_by_text(text_query, candidate_count)
            query_label = text_query.strip() or "empty text query"
        else:
            results = search_index.search_by_image(
                image_query,
                candidate_count,
                text_hint=text_query,
            )
            hint = text_query.strip()
            query_label = "uploaded image"
            if hint:
                query_label += f" with text hint: {hint}"
            if image_query is None:
                query_label = "no image"
    except Exception as error:
        return [], f"Search unavailable: {error}", [], [], gr.update(choices=[], value=None), None, ""

    results = filter_results(results, min_score, only_same_category)[: int(top_k)]
    if not results:
        return (
            [],
            f"No results for {query_label}. Try lowering the minimum score.",
            [],
            [],
            gr.update(choices=[], value=None),
            None,
            "",
        )

    overview = (
        f"<div class='status-strip'>Showing <b>{len(results)}</b> results for "
        f"<b>{query_label}</b>. Indexed images: <b>{len(search_index.image_paths)}</b>.</div>"
    )
    choices = result_choices(results)
    return (
        gallery_items(results),
        overview,
        result_table(results),
        serialize_results(results),
        gr.update(choices=choices, value=choices[0]),
        results[0].path,
        f"Selected: {Path(results[0].path).name}",
    )


def select_result_file(
    results_state: list[dict[str, Any]] | None,
    result_choice: str | None,
) -> tuple[str | None, str]:
    results = deserialize_results(results_state)
    if not results:
        return None, "No search results selected."
    index = selected_index(result_choice)
    if index is None:
        return None, "Choose a result first."
    if index < 0 or index >= len(results):
        return None, f"Choose a result from 1 to {len(results)}."

    selected = results[index]
    return selected.path, f"Selected result {index + 1}."


def preview_result(
    results_state: list[dict[str, Any]] | None,
    result_choice: str | None,
) -> tuple[str | None, str]:
    return select_result_file(results_state, result_choice)


def add_to_favorites(
    results_state: list[dict[str, Any]] | None,
    result_choice: str | None,
) -> str:
    selected_path, message = select_result_file(results_state, result_choice)
    if selected_path is None:
        return message

    source = Path(selected_path)
    if not source.exists():
        return f"Cannot find {source}."

    FAVORITES_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = FAVORITES_DIR / f"{timestamp}_{source.name}"
    shutil.copy2(source, destination)
    return f"Saved to favorites: {destination}"


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Image Search Lab 3") as demo:
        gr.Markdown("# Image Search")

        results_state = gr.State([])

        with gr.Row():
            with gr.Column(scale=1, elem_classes=["query-panel"]):
                mode = gr.Radio(["Text", "Image"], value="Text", label="Search mode")
                text_query = gr.Textbox(
                    label="Text query / image hint",
                    placeholder="Try: kiwi, banana, orange juice, oat milk",
                )
                with gr.Row():
                    kiwi_button = gr.Button("Kiwi", size="sm")
                    banana_button = gr.Button("Banana", size="sm")
                    apple_button = gr.Button("Apple", size="sm")
                    juice_button = gr.Button("Orange Juice", size="sm")
                image_query = gr.Image(
                    label="Image query",
                    type="pil",
                    sources=["upload", "clipboard"],
                    height=400,
                )
                with gr.Row():
                    top_k = gr.Slider(
                        minimum=1,
                        maximum=20,
                        value=8,
                        step=1,
                        label="Returned images",
                    )
                    min_score = gr.Slider(
                        minimum=0,
                        maximum=1.2,
                        value=0,
                        step=0.02,
                        label="Minimum score",
                    )
                only_same_category = gr.Checkbox(
                    value=False,
                    label="Only same category",
                )
                search_button = gr.Button(
                    "Search",
                    variant="primary",
                    elem_classes=["primary-action"],
                )

            with gr.Column(scale=2):
                overview = gr.Markdown(
                    "<div class='status-strip'>Index ready: 5522 local grocery images.</div>"
                )
                gallery = gr.Gallery(
                    label="Results",
                    columns=[4],
                    rows=[2],
                    object_fit="cover",
                    height=840,
                    allow_preview=True,
                )

        with gr.Row():
            table = gr.Dataframe(
                headers=["Rank", "Ranking score"],
                datatype=["number", "number"],
                interactive=False,
                label="Result overview",
            )

        with gr.Row():
            with gr.Column(scale=1):
                result_select = gr.Dropdown(
                    choices=[],
                    label="Selected result",
                    interactive=True,
                )
                with gr.Row():
                    favorite_button = gr.Button("Add to favorites")
                    download_button = gr.Button("Prepare download")
                action_status = gr.Textbox(label="Action status", interactive=False)
                download_file = gr.File(label="Download selected image")
            with gr.Column(scale=1):
                selected_preview = gr.Image(
                    label="Selected image",
                    interactive=False,
                    height=300,
                )

        kiwi_button.click(lambda: "kiwi", outputs=text_query)
        banana_button.click(lambda: "banana", outputs=text_query)
        apple_button.click(lambda: "apple", outputs=text_query)
        juice_button.click(lambda: "orange juice", outputs=text_query)

        search_button.click(
            run_search,
            inputs=[mode, text_query, image_query, top_k, min_score, only_same_category],
            outputs=[
                gallery,
                overview,
                table,
                results_state,
                result_select,
                selected_preview,
                action_status,
            ],
        )
        result_select.change(
            preview_result,
            inputs=[results_state, result_select],
            outputs=[selected_preview, action_status],
        )
        favorite_button.click(
            add_to_favorites,
            inputs=[results_state, result_select],
            outputs=action_status,
        )
        download_button.click(
            select_result_file,
            inputs=[results_state, result_select],
            outputs=[download_file, action_status],
        )

    return demo


if __name__ == "__main__":
    build_ui().launch(css=APP_CSS)
