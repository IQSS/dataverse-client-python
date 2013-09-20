stage { 'repos': before => Stage['packages'] }

stage { 'packages': before => Stage['main'] }

class {
    'repos': stage => repos;
    'packages': stage => packages;
    'sysprep': stage => repos;
}
