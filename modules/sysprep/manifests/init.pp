class sysprep {

  file { '/etc/sysconfig/iptables':
    source => 'puppet:///modules/bucket/etc/sysconfig/iptables',
    notify => Service['iptables'],
    owner  => 'root',
    group  => 'root',
    mode   => '0600',
  }

  service { 'iptables':
    ensure => running
  }
}
