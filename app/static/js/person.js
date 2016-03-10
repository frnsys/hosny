define([], function() {
  var colors = [
    0x555555,
    0xff4444,
    0xffff44,
    0x44ffff
  ];

  var Person = function(radius, velocity) {
    var color = _.sample(colors),
        geometry = new THREE.SphereGeometry(radius),
        material = new THREE.MeshBasicMaterial({
          color: color
        });
    this.mesh = new THREE.Mesh(geometry, material);
    this.distanceTraveled = {x:0, z:0};
    this.velocity = velocity;
  };

  Person.prototype = {
    update: function() {
      this.mesh.position.x += this.velocity.x;
      this.mesh.position.z += this.velocity.z;
      this.distanceTraveled.x += Math.abs(this.velocity.x);
      this.distanceTraveled.z += Math.abs(this.velocity.z);
    }
  };

  return Person;
});
