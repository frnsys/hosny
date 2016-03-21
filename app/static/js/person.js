define([], function() {
  var colors = [
    0xffffff,
    0x000000,
    0xff4444,
    0xffff44,
    0x44ffff,
    0x44ff44,
    0xff44ff,
    0x4444ff,
    0x555555
  ];
  var radius = 0.2;

  var Person = function(data) {
    var color = colors[data.race-1],
        material = new THREE.MeshLambertMaterial({
          color: color
        }),
        geometry;

    // flatland-esque rankings
    if (data.firm_owner) {
        geometry = new THREE.SphereGeometry(radius);
    } else if (data.employed) {
        geometry = new THREE.BoxGeometry(radius*1.5, radius*1.5, radius*1.5);
    } else {
        geometry = new THREE.TetrahedronGeometry(radius*1.5);
    }

    this.mesh = new THREE.Mesh(geometry, material);
    this.distanceTraveled = {x:0, z:0};
    this.velocity = {x:0, z:0};
  };

  Person.prototype = {
    radius: radius,

    update: function() {
      this.mesh.position.x += this.velocity.x;
      this.mesh.position.z += this.velocity.z;
      this.distanceTraveled.x += Math.abs(this.velocity.x);
      this.distanceTraveled.z += Math.abs(this.velocity.z);
    },

    wander: function(velocity) {
      this.distanceTraveled = {x:0, z:0};
      this.velocity = velocity;
    },

    stop: function() {
      this.velocity = 0;
    }
  };

  return Person;
});
