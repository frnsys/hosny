define([
  'city'
], function(City) {
  var fps = 30;
  var Simulation = function() {
      var width = 960,
          height = 500,
          aspect = width/height,
          D = 1,
          light = new THREE.PointLight(0xffffff, 1, 40);

      this.scene = new THREE.Scene();
      this.renderer = new THREE.WebGLRenderer({alpha: true, canvas: document.getElementById("stage")});
      this.camera = new THREE.OrthographicCamera(-D*aspect, D*aspect, D, -D, 1, 1000),

      this.renderer.setSize(width, height);
      this.renderer.setClearColor(0xffffff, 0);
      this.scene.add( new THREE.AmbientLight(0x4000ff) );

      light.position.set(15, 20, 15);
      this.scene.add(light);

      light = new THREE.HemisphereLight( 0xffffbb, 0x080820, 1);
      this.scene.add(light);

      this.camera.zoom = 0.1;
      this.camera.position.set(20, 20, 20);
      this.camera.lookAt(this.scene.position);
      this.camera.updateProjectionMatrix();
  };

  Simulation.prototype = {
    // setup the scene
    setup: function(rows, cols, margin, population, buildings, config) {
        this.city = new City(rows, cols, margin, population, buildings, config, this.scene);
    },

    render: function() {
        this.renderer.render(this.scene, this.camera);
    },

    pause: function() {
      this.loop.pause();
    },

    resume: function() {
      this.loop.resume();
    },

    start: function() {
      this.loop = new RecurringTimer(this.update.bind(this), fps);
    },

    update: function() {
      this.city.update();
      this.render();
    }
  };

  return Simulation;
});
