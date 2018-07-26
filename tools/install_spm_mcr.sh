if [ ! -d $HOME/mcr ]
then
  echo "destinationFolder=$HOME/mcr" > $HOME/mcr_options.txt
  echo "agreeToLicense=yes" >> $HOME/mcr_options.txt
  echo "outputFile=/tmp/matlabinstall_log" >> $HOME/mcr_options.txt
  echo "mode=silent" >> $HOME/mcr_options.txt
  mkdir -p $HOME/matlab_installer
  wget -nc http://www.mathworks.com/supportfiles/downloads/R2015a/deployment_files/R2015a/installers/glnxa64/MCR_R2015a_glnxa64_installer.zip -O $HOME/matlab_installer/installer.zip
  unzip $HOME/matlab_installer/installer.zip -d $HOME/matlab_installer/
  $HOME/matlab_installer/install -inputFile $HOME/mcr_options.txt
  rm -rf $HOME/matlab_installer $HOME/mcr_options.txt
fi

if [ ! -d $HOME/spm12 ]
then
  wget http://www.fil.ion.ucl.ac.uk/spm/download/restricted/utopia/dev/spm12_r6472_Linux_R2015a.zip -O $HOME/spm12.zip
  unzip $HOME/spm12.zip -d $HOME
  rm -rf $HOME/spm12.zip
fi
