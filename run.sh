setup_install(){
    if pip list | grep -Fq "virtualenv"; then
        echo " Library [ virtualenv ] is installed"
        pip show virtualenv
    else
        echo " Installing..." 
        pip install virtualenv
    fi

    cd TOMI-env
    source Scripts/activate
    cd ..
    echo -e " TOMI processing...\n"
}

setup_install

python TOMI-project/Main.py
# echo -e "\nEnd processing..."
# read
