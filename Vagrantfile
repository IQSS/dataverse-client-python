Vagrant::Config.run do |config|

  config.vm.box = "centos"
  config.vm.box_url = "https://dl.dropbox.com/u/7225008/Vagrant/CentOS-6.3-x86_64-minimal.box"

  #config.vm.boot_mode = :gui
  config.vm.share_folder "downloads", "/downloads", "downloads"
  config.vm.share_folder "dvn_client", "/home/vagrant/dvn_client", "dvn_client"
  #config.vm.forward_port 8080, 8888
  #config.vm.forward_port 8181, 9999

  config.vm.customize ["modifyvm", :id, "--memory", 2048]

  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = "manifests"
    puppet.module_path = "modules"
    puppet.manifest_file  = "init.pp"
  end

end
