require([
  'city',
  'graph'
], function(City, Graph) {
  var fps = 30;
  var game = {
    // setup the scene
    setup: function(rows, cols, margin, population, buildings, config) {
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

  var socket = io();

  var rows = 6,
      cols = 6,
      max_tenants = 10;

  $(function() {
      $(".setup-simulation").on("submit", function(ev) {
        ev.preventDefault();
        $('.overlay').fadeOut();

        $.ajax({
          type: "POST",
          url: "/setup",
          data: JSON.stringify({
            person: {
              race: $('[name=race]').val(),
              education: $('[name=education]').val(),
              employment: $('[name=employment]').val(),
            },
            world: {
              minWage: $('[name=minWage]').val(),
              desiredWage: $('[name=desiredWage]').val(),
              n_buildings: rows * cols,
              max_tenants: max_tenants
            }
          }),
          contentType: "application/json",
          success: function(data, textStatus, jqXHR) {
            $('.step-simulation').show();
          }
        });

        return false;
      });

      $('.step-simulation').on('click', function() {
        $.ajax({
          type: "POST",
          url: "/step"
        })
      });

      socket.on("setup", function(data){
        var config = {
          maxTenants: max_tenants
        }
        game.setup(rows, cols, 0.5, data.population, data.buildings, config);
        game.start();
      });

      socket.on("twooter", function(data){
        data.username = slugify(data.name);
        //console.log(data);
        $(".twooter-feed").prepend(renderTemplate('twoot', data));
      });

      socket.on("buildings", function(data){
        var id = data.id;
        if (data.event === 'added_tenant') {
          game.city.buildings[id].add(data.tenant);
        } else if (data.event === 'removed_tenant') {
          game.city.buildings[id].removeById(data.tenant.id);
        }
      });

      var graphs = {
        mean_wage: new Graph(".graphs", "mean_wage", 650, 200, "mean wage"),
        mean_equip_price: new Graph(".graphs", "mean_equip_price", 650, 200, "mean equip price"),
        mean_consumer_good_price: new Graph(".graphs", "mean_consumer_good_price", 650, 200, "mean consumer good price")
      };

      socket.on("graph", function(data){
        if (data.graph in graphs) {
          var graph = graphs[data.graph];
          graph.update(data.data);
        }
      });

      // Advancing from setup screen 1 to screen 2
      var i = 0;
      $(".next").on("click", function() {
        $("fieldset").eq(i).removeClass("show").addClass("hide");
        $("fieldset").eq(i+1).removeClass("hide").addClass("show");
        i++;
      });

      $(".twooter-feed").on('click', '.twoot-author', function() {
        var id = $(this).data('id');
        if (!id) { return; }
        $.ajax({
          type: "GET",
          url: "/person/" + id,
          success: function(data) {
            $('.overlay').fadeIn();
            $('.overlay-content').text(JSON.stringify(data));
          }
        });
      });
  });

});