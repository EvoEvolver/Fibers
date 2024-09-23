import os

import jsonlines
from moduler.decorator import example

curr_dir = os.path.dirname(os.path.abspath(__file__))

url_to_dataset = {
    "QuALITY.v1.0.1.train": "https://raw.githubusercontent.com/nyu-mll/quality/main/data/v1.0.1/QuALITY.v1.0.1.train",
    "QuALITY.v1.0.1.dev": "https://raw.githubusercontent.com/nyu-mll/quality/main/data/v1.0.1/QuALITY.v1.0.1.dev",
    "QuALITY.v1.0.1.test": "https://raw.githubusercontent.com/nyu-mll/quality/main/data/v1.0.1/QuALITY.v1.0.1.test",
    "QuALITY.v1.0.1.htmlstripped.dev": "https://raw.githubusercontent.com/nyu-mll/quality/main/data/v1.0.1/QuALITY.v1.0.1.htmlstripped.dev",
}


def download_dataset(name):
    if name not in url_to_dataset:
        raise ValueError(f"Unknown dataset {name}")
    url = url_to_dataset[name]
    dataset_path = os.path.join(curr_dir, name)
    print(f"Downloading dataset {name} from {url} to {dataset_path}")
    os.system(f"curl {url} -o {dataset_path}")


def iter_dataset(name):
    dataset_path = os.path.join(curr_dir, name)
    if not os.path.exists(dataset_path):
        download_dataset(name)
    with jsonlines.open(dataset_path) as reader:
        for obj in reader:
            yield obj


def extract_dataset(name, number):
    i = 0
    for obj in iter_dataset(name):
        if i == number:
            return obj
        i += 1
    raise ValueError(f"Dataset {name} has only {i} examples")


@example
def example_usage():
    from fibers.data_loader.html_to_tree import html_to_tree
    #from fibers.compose.pipeline_text.tree_preprocess import preprocess_text_tree
    # 100
    data = extract_dataset("QuALITY.v1.0.1.dev", 7)
    tree = html_to_tree(data["article"], to_markdown=False)
    #preprocess_text_tree(tree, fat_limit=150)
    tree.display()


if __name__ == '__main__':
    example_usage()
