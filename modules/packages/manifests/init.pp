class packages {

  $packages_to_install = [
    'python-setuptools',
    'python-devel',
    'libxml2-devel',
    'libxslt-devel',
    'python-argparse',
    'python-lxml',
    # common tools
    'unzip',
    'git',
    'vim-enhanced',
    'ack',
    'mlocate',
  ]

  package { $packages_to_install:
    ensure => installed,
  }

  # FIXME: make this idempotent
  exec {"install swordv2 python client":
    path     => "/bin:/usr/bin",
    command  => "git clone https://github.com/pjbull/python-client-sword2.git /swordv2 && cd /swordv2 && python setup.py install",
    provider => "shell"
  }
}
