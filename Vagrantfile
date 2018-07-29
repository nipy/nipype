VAGRANTFILE_API_VERSION = "2"

$script = <<SCRIPT

# Following section commented out as gridengine requires interactive
# components
# # Install neurodebian repo
# bash <(wget -q -O- http://neuro.debian.net/_files/neurodebian-travis.sh)
#
# # Install grid engine
# sudo apt-get install -qq gridengine-master gridengine-exec gridengine-client gridengine-qmon
# # Configure: http://wiki.unixh4cks.com/index.php/Setting_up_Sun_Grid_Engine_on_Ubuntu
# sudo -u sgeadmin qconf -am vagrant
# qconf -au vagrant users
# qconf -as neuro
# qconf -ahgrp @allhosts
# qconf -aattr hostgroup hostlist neuro @allhosts
# qconf -aq main.q
# qconf -aattr queue hostlist @allhosts main.q
# qconf -aattr queue slots "2, [neuro=3]" main.q

# install anaconda
wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
chmod +x miniconda.sh
./miniconda.sh -b
echo "export PATH=$HOME/miniconda3/bin:\\$PATH" >> .bashrc

# install nipype dependencies
$HOME/miniconda3/bin/conda update --yes conda
$HOME/miniconda3/bin/conda install --yes pip scipy networkx lxml future simplejson
$HOME/miniconda3/bin/conda install --yes python-dateutil jupyter matplotlib
$HOME/miniconda3/bin/pip install nibabel
$HOME/miniconda3/bin/pip install prov
$HOME/miniconda3/bin/pip install xvfbwrapper
$HOME/miniconda3/bin/pip install traits
$HOME/miniconda3/bin/pip install https://github.com/nipy/nipype/archive/master.zip
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.define :engine do |engine_config|

    engine_config.vm.box = "gridneuro"
    #engine_config.vm.box_url = "http://files.vagrantup.com/precise64.box"
    engine_config.vm.box_url = "https://dl.dropboxusercontent.com/u/363467/precise64_neuro.box"
    #engine_config.vm.network :forwarded_port, guest: 80, host: 8080

    #engine_config.vm.network :public_network, :bridge => 'en0: Wi-Fi (AirPort)'
    engine_config.vm.network :private_network, ip: "192.168.100.20"
    engine_config.vm.hostname = 'neuro'
    #engine_config.vm.synced_folder "../software", "/software"
    #engine_config.vm.synced_folder "../data", "/data"

    engine_config.vm.provider :virtualbox do |vb|
      vb.customize ["modifyvm", :id, "--cpuexecutioncap", "50"]
      vb.customize ["modifyvm", :id, "--ioapic", "on"]
      vb.customize ["modifyvm", :id, "--memory", "4096"]
      vb.customize ["modifyvm", :id, "--cpus", "4"]
    end

    engine_config.vm.provision "shell", :privileged => false, inline: $script
  end
end
