
# Fibers: knowledge with bones

<div style="text-align: center;">
<a href="https://f.evoevo.org/html/project_tree.html">ProjectTree</a>
</div>

## Installation

Currently, Fibers is not ready for production usage. Please refer to  [Development](https://f.evoevo.org/development) for development usage.

## Development

- In order to use OpenAI API, the environment variables `OPENAI_API_KEY` should be set to your API key.
- PyCharm is recommended.

You can set up your development environment by the following commands. You must install `Moduler` first, because `Fibers` depends on it.
```shell
git clone https://github.com/EvoEvolver/Fibers.git
git clone https://github.com/EvoEvolver/Moduler.git
```

If you want to see the visualization in React. Please clone the following repo:
```shell
git clone https://github.com/EvoEvolver/Forest.git
```

If you are using PyCharm, do the following steps:
- Go to settings -> Project structure
- Add `Moduler` and `Fibers` to the content roots
- Add `Forest` to the content roots if you want to see visualization in React.
- Install the dependencies by `pip`

If you are using VSCode, you can make install the packages by
```shell
pip install -e Moduler
pip install -e Fibers
```



## Acknowledgement

This project is led by [the matter lab](https://www.matter.toronto.edu/) at the University of Toronto.