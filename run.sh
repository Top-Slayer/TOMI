setup_install(){
    if pip list | grep -Fq "virtualenv"; then
        echo " Library [ virtualenv ] already installed"
        pip list | grep virtualenv
    else
        echo " Installing..." 
        python -m pip install virtualenv
    fi

    if [ -d "TOMI-env" ]; then
        echo " Folder TOMI-env exists."
    else
        python -m venv env # create virtual environment folder
    fi

    source TOMI-env/Scripts/activate
    python -m pip install --upgrade pip
}

setup_install
pip install -r requirements.txt
# pip freeze > requirements.txt

clear
echo -e "\n ------------------------------------------------ \n"
echo -e " TOMI processing...\n"

cd TOMI-project
python Main.py
echo -e "\nEnd processing..."
read
