define([], function() {
  var colors = [
    0x555555,
    0xff4444,
    0xffff44,
    0x44ffff
  ];

  var Building = function(type, side) {
    var height = 1 + Math.random() * 4,
        color = _.sample(colors),
        geometry = new THREE.BoxGeometry(side, height, side),
        material = new THREE.MeshLambertMaterial({
          color: color
        });
    this.mesh = new THREE.Mesh(geometry, material);
  };

  Building.type = {
    Office: 0,
    Retail: 1,
    Public: 2,
    Residence: 3
  };


  return Building;
});
