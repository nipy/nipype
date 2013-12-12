VAGRANTFILE_API_VERSION = "2"

$script = <<SCRIPT
echo I am provisioning...
echo `whoami`
sudo apt-get update -qq
wget http://repo.continuum.io/miniconda/Miniconda-2.2.2-Linux-x86_64.sh -O miniconda.sh
chmod +x miniconda.sh
./miniconda.sh -b
echo `whoami`
echo "export PATH=$HOME/anaconda/bin:\\$PATH" >> .bashrc
# sudo bash <(wget -q -O- http://neuro.debian.net/_files/neurodebian-travis.sh)
$HOME/anaconda/bin/conda install --yes pip numpy scipy nose traits networkx
$HOME/anaconda/bin/conda install --yes dateutil ipython-notebook
$HOME/anaconda/bin/pip install nibabel --use-mirrors
$HOME/anaconda/bin/pip install https://github.com/RDFLib/rdflib/archive/master.zip
$HOME/anaconda/bin/pip install https://github.com/satra/prov/archive/enh/rdf.zip
$HOME/anaconda/bin/pip install https://github.com/nipy/nipype/archive/master.zip
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.define :engine do |engine_config|

    engine_config.vm.box = "gridneuro"
    engine_config.vm.box_url = "https://dl.dropboxusercontent.com/u/363467/precise64_neuro.box"
    engine_config.vm.network :forwarded_port, guest: 80, host: 8080

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
