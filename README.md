
# Fibers

<div style="text-align: center;">
<a href="https://f.evoevo.org/html/project_tree.html">ProjectTree</a>
</div>

## Installation

Currently, Fibers is not ready for production usage. Please refer to  [Development](https://f.evoevo.org/development) for development usage.

## Development

- In order to use OpenAI API, the environment variables `OPENAI_API_KEY` should be set to your API key.
- PyCharm is recommended.

### Install by script

1. Find a good place to put the project. `cd` to it.
2. Run the following script in the terminal.
```shell
source <(curl -s https://raw.githubusercontent.com/EvoEvolver/Fibers/main/script/setup_env.sh)
```
3. Setup your OpenAI API key
```shell
source <(curl -s https://raw.githubusercontent.com/EvoEvolver/Fibers/main/script/set_open_api_key.sh)
```

You should update your project frequently by running the following script.
```shell
source <(curl -s https://raw.githubusercontent.com/EvoEvolver/Fibers/main/script/update_projects.sh)
``` 

### Install manually

You need to have `node` and `npm` installed for the development environment. For this, you can run
```shell
conda install nodejs
```

You can set up your development environment by the following steps. 
```shell
conda create -n Evo python=3.10
conda activate Evo # You can replace the name
conda install nodejs # if you haven't installed it
mkdir EvoEvolver # Create the folder for the projects
cd EvoEvolver
git clone https://github.com/EvoEvolver/Fibers.git
git clone https://github.com/EvoEvolver/Moduler.git
git clone https://github.com/EvoEvolver/Forest.git
```

If you are using PyCharm, do the following steps:
- Go to settings -> Project structure
- Add `Moduler`, `Forest` and  `Fibers` to the content roots
- Install the dependencies by `pip`

If you are using VSCode, you can make install the packages by
```shell
pip install -e Moduler
pip install -e Forest
pip install -e Fibers
```

Add your OpenAI API key to the environment variables. You can do this by adding the following line to your `.bashrc` or `.zshrc` file. Remember to replace `your_api_key` with your actual API key starting with `sk-`.


For Linux:
```shell
echo "export OPENAI_API_KEY='your_api_key'" >> ~/.bashrc
```

For MacOS:
```shell
echo "export OPENAI_API_KEY='your_api_key'" >> ~/.zshrc
```


## Acknowledgement

This project is led by [the matter lab](https://www.matter.toronto.edu/) at the University of Toronto.