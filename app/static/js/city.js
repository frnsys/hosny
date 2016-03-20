define([
  'person',
  'building'
], function(Person, Building) {
  var City = function(rows, cols, margin, population, scene) {
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
    this.spawn(population);
  };

  City.prototype = {
    // for conveniently placing things with the offset
    place: function(obj, x, y, z) {
      obj.position.set(x + this.offset.x, y, z + this.offset.z);
      this.scene.add(obj);
    },

    remove: function(obj) {
      this.scene.remove(obj);
    },

    update: function() {
      var self = this;
      _.each(this.population, function(p) {
        var radius = p.radius;
        p.update();

        // destroy when out of the city
        if (p.distanceTraveled.x > self.gridWidth + 2*radius || p.distanceTraveled.z > self.gridDepth + 2*radius) {
          self.scene.remove(p.mesh);
          self.placePersonDelayed(p);
        }
      });
    },

    // spawn the city
    spawn: function(population) {
      this.spawnBuildings();
      this.spawnRoads();

      var self = this;
      for (var i=0; i < population.length; i++) {
        // stagger
        var person = new Person(population[i]);
        this.population.push(person);
        this.placePersonDelayed(person);
      }

      //this.origin();
    },

    spawnBuilding: function(row, col) {
      var x = row * this.fullSide,
          z = col * this.fullSide,
          building = new Building.Building(x, z, this),
          tenant = new Building.Tenant('Business');
      building.add(tenant);
      building.add(new Building.Tenant('Residential'));
      building.add(new Building.Tenant('Hospital'));
      building.add(new Building.Tenant('Business'));
      building.add(new Building.Tenant('Hospital'));
      building.add(new Building.Tenant('Residential'));
      building.add(new Building.Tenant('Hospital'));
      building.add(new Building.Tenant('Business'));
      building.add(new Building.Tenant('Hospital'));
      building.add(new Building.Tenant('Residential'));
    },

    spawnBuildings: function() {
      for (var i=0; i < this.rows; i++) {
        var row = [];
        for (var j=0; j < this.cols; j++) {
          this.spawnBuilding(i, j);
        }
      }
    },

    placePerson: function(person) {
      var radius = person.radius,
          x = 0,
          z = 0,
          velocity = {x:0, z:0};
      if (Math.random() < 0.5) {
        z = _.sample([-radius, this.gridDepth + radius]);
        var col = _.random(0, this.cols);
        x = (col-1) * this.fullSide + (this.side/2 + this.margin);
        velocity.z = z < 0 ? 0.1 : -0.1;

        // "lanes", people keep to the right
        if (z == -radius) {
          x -= radius;
        } else {
          x += radius;
        }
      } else {
        x = _.sample([-radius, this.gridWidth + radius]);
        var row = _.random(0, this.rows);
        z = (row-1) * this.fullSide + (this.side/2 + this.margin);
        velocity.x = x < 0 ? 0.1 : -0.1;

        // "lanes", people keep to the right
        if (x == -radius) {
          z -= radius;
        } else {
          z += radius;
        }
      }
      this.place(person.mesh, x - radius, radius, z - radius);
      person.wander(velocity);
    },

    placePersonDelayed: function(person) {
      var self = this;
      setTimeout(function() {
        self.placePerson(person);
      }, Math.random() * 5000);
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
