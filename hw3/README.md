# Lab 3 Image Search

This project is an image search system for the Human-Computer Interaction Lab 3 assignment. It uses Gradio to build the user interface and CLIP (`openai/clip-vit-base-patch32`) to support both text-to-image search and image-to-image search.

The current local index contains 5522 grocery product images, and each image is represented by a 512-dimensional CLIP embedding.

## Project Structure

| Path | Description |
| --- | --- |
| `app.py` | Gradio user interface |
| `search.py` | CLIP loading, encoding, ranking, and filtering logic |
| `build_index.py` | Builds local image embeddings and index files |
| `requirements.txt` | Python dependencies |
| `data/images/` | Dataset images |
| `index/` | Prebuilt local image index |
| `favorites/` | Images saved from search results |
| `reports/` | Report files |

## Environment

Python 3.10 or later is recommended.

Install the required packages:

```bash
pip install -r requirements.txt
```

The dependencies include:

- `gradio`
- `numpy`
- `pillow`
- `torch`
- `transformers`

The first time the program loads CLIP, it may download `openai/clip-vit-base-patch32` from Hugging Face. If the model has already been cached locally, the program will use the local cache first.

## Dataset

The project uses GroceryStoreDataset:

```text
https://github.com/marcusklasson/GroceryStoreDataset
```

The dataset should be placed under:

```text
data/images/
```

This submitted project already includes the dataset directory and a prebuilt index under `index/`, so you can run the interface directly after installing dependencies.

## Build or Rebuild the Index

If `index/` is already present, this step can be skipped.

To rebuild the image index, run:

```bash
python build_index.py
```

Optional arguments:

```bash
python build_index.py --image-dir data/images --index-dir index --batch-size 16
```

After building, the following files will be generated:

```text
index/image_embeddings.npy
index/image_paths.json
index/metadata.json
```

## Run the Application

Start the Gradio interface:

```bash
python app.py
```

After the program starts, open the local URL printed in the terminal. It is usually:

```text
http://127.0.0.1:7860
```

## How to Use

1. Select the search mode: `Text` or `Image`.
2. In `Text` mode, enter a product name or description, such as `kiwi`, `banana`, or `orange juice`.
3. In `Image` mode, upload a query image. You may also enter a text hint to improve the ranking.
4. Adjust the returned image count, minimum score, or same-category filter if needed.
5. Click `Search`.
6. Review the ranked image results in the gallery and result table.
7. Select a result to preview it.
8. Click `Add to favorites` to save the selected image to `favorites/`, or click `Prepare download` to download it.

## Main Features

- Text-to-image search
- Image-to-image search
- Optional hybrid search using an uploaded image and a text hint
- Ranked results based on CLIP similarity and lightweight category boosting
- Query image preview
- Quick query buttons for common examples
- Adjustable number of returned images
- Minimum score filtering
- Same-category filtering
- Result preview, favorites, and download support

## Troubleshooting

If the program reports that the image index cannot be found, run:

```bash
python build_index.py
```

If the CLIP model cannot be downloaded, check the network connection or prepare the model locally and pass the local model path with:

```bash
python build_index.py --model-name path/to/local/clip-model
```

The PowerShell message about disabled profile scripts does not affect this project. It is caused by the local PowerShell execution policy and can be ignored if the Python command runs normally.
