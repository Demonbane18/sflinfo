# SFLINFO

## Prerequisites

Python >= 3.6
## Install
    cd ~
    git clone git@github.com:ktnoc/sflinfo.git
    cd sflinfo/
    virtualenv venv
    source venv/bin/activate
    python setup.py install
or
    pip install -r requirements.txt

## Commander_mode

    cd ~
    cd sflinfo/
    echo 'api_keys = {"polygonscan": "FFFFFF", "alchemy": "SSSSSSSS"}' > secretsettings.py
    sudo ./service.webapp.define

### Pub over cloudflare

Install

    ansible-playbook -i hosts/d playbooks/sflinstall.yml --extra-vars "ansible_sudo_pass=x ansible_user=ubuntu ansible_ssh_pass=x ansible_ssh_extra_args='-o StrictHostKeyChecking=no'"

Deploy

    ansible-playbook -i hosts/d playbooks/sfldeploy.yml --extra-vars "ansible_sudo_pass=x ansible_user=ruser ansible_ssh_pass=x ansible_ssh_extra_args='-o StrictHostKeyChecking=no'"
