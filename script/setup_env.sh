conda create -n Evo python=3.10
conda activate Evo # You can replace the name
conda install nodejs # if you haven't installed it
mkdir EvoEvolver # Create the folder for the projects
cd EvoEvolver
git clone https://github.com/EvoEvolver/Moduler.git
git clone https://github.com/EvoEvolver/Forest.git
git clone https://github.com/EvoEvolver/Fibers.git
pip install -e Moduler
pip install -e Forest
pip install -e Fibers