define([
  'person',
  'building'
], function(Person, Building) {
  var City = function(rows, cols, margin, scene) {
    this.rows = rows;
    this.cols = cols;
    this.side = 1;
    this.margin = margin;
    this.scene = scene;

    this.fullSide = this.side + 2*this.margin;

    this.gridWidth = this.fullSide * cols;
    this.gridDepth = this.fullSide * rows;

    // extra offset to compensate for building height
    var xOffset = 3,
        zOffset = 3;

    // for centering the city
    this.offset = {
      x: -this.gridWidth/2 + xOffset,
      z: -this.gridDepth/2 + zOffset
    }

    // initialize the grid
    this.grid = [];
    for (var i=0; i < rows; i++) {
      var row = [];
      for (var j=0; j < cols; j++) {
        row.push(null);
      }
      this.grid.push(row);
    }

    this.population = [];
    this.spawn();
  };

  City.prototype = {
    // for conveniently placing things with the offset
    place: function(obj, x, y, z) {
      obj.position.set(x + this.offset.x, y, z + this.offset.z);
      this.scene.add(obj);
    },

    update: function() {
      var self = this;
      _.each(this.population, function(p) {
        var radius = p.mesh.geometry.parameters.radius;
        p.update();

        // destroy when out of the city
        if (p.distanceTraveled.x > self.gridWidth + 2*radius || p.distanceTraveled.z > self.gridDepth + 2*radius) {
          self.scene.remove(p.mesh);
          self.population = _.without(self.population, p);
          setTimeout(function() {
            self.spawnPerson();
          }, Math.random() * 5000);
        }
      });
    },

    // spawn the city
    spawn: function() {
      this.spawnBuildings();
      this.spawnRoads();

      var self = this;
      for (var i=0; i < 100; i++) {
        // stagger
        setTimeout(function() {
          self.spawnPerson();
        }, Math.random() * 5000);
      }

      //this.origin();
    },

    spawnBuilding: function(row, col) {
      var building = new Building(Building.type.Office, this.side),
          x = row * this.fullSide,
          z = col * this.fullSide;
      this.place(building.mesh, x, building.mesh.geometry.parameters.height/2, z);
    },

    spawnBuildings: function() {
      for (var i=0; i < this.rows; i++) {
        var row = [];
        for (var j=0; j < this.cols; j++) {
          this.spawnBuilding(i, j);
        }
      }
    },

    spawnPerson: function() {
      var radius = 0.2,
          x = 0,
          z = 0,
          velocity = {x:0, z:0};
      if (Math.random() < 0.5) {
        z = _.sample([-radius, this.gridDepth + radius]);
        var col = _.random(0, this.cols);
        x = (col-1) * this.fullSide + (this.side/2 + this.margin);
        velocity.z = z < 0 ? 0.1 : -0.1;
      } else {
        x = _.sample([-radius, this.gridWidth + radius]);
        var row = _.random(0, this.rows);
        z = (row-1) * this.fullSide + (this.side/2 + this.margin);
        velocity.x = x < 0 ? 0.1 : -0.1;
      }

      var person = new Person(radius, velocity);
      this.place(person.mesh, x - radius, radius, z - radius);
      this.population.push(person);
    },

    spawnRoads: function() {
      var planeGeometry = new THREE.PlaneGeometry(this.gridWidth, this.gridDepth),
          planeMaterial = new THREE.MeshLambertMaterial( {color: 0x333333, side: THREE.DoubleSide} ),
          plane = new THREE.Mesh( planeGeometry, planeMaterial );
      plane.rotation.x = Math.PI / 2;
      this.place(plane, this.gridWidth/2 - this.margin, 0, this.gridDepth/2 - this.margin);
    },

    // to easily visually identify where the origin is (for debugging)
    origin: function() {
      var geometry = new THREE.BoxGeometry(0.2,50,0.2),
          material = new THREE.MeshLambertMaterial({
            color: 0x000000
          }),
          cube = new THREE.Mesh(geometry, material);
      cube.position.set(0,0,0);
      this.scene.add(cube);
    }
  }

  return City;
});
