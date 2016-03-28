require([
  'simulation'
], function(Simulation) {
  var sim = new Simulation(),
      rows = 6,
      cols = 6,
      max_tenants = 10,
      socket = io('/simulation'),
      config = {
        patient_zero_prob: 0.01,
        contact_rate: 0.1,
        transmission_rate: 0.1,
        sickness_severity: 0.01,
        tax_rate: 0.3,
        tax_rate_increment: 0,
        welfare_increment: 0,
        welfare: 10,
        consumer_good_utility: 1,
        rent: 1000,
        labor_cost_per_good: 2,
        material_cost_per_good: 2,
        labor_per_worker: 50,
        labor_per_equipment: 50,
        supply_increment: 10,
        profit_increment: 10,
        wage_increment: 1,
        extravagant_wage_range: 100,
        residence_size_limit: 100,
        base_min_consumption: 0,
        wage_under_market_multiplier: 1,
        min_business_capital: 50000,
        starting_wage: 5,
        desiredWage: 5,
        starting_welfare_req: 10000
      };

  console.log(config);

  $(function() {
      $(".next").on("click", function(ev) {
        ev.preventDefault();
        $('.overlay').fadeOut();
        var numOfPlayers = Math.floor((Math.random() * 10) + 1);

        for(var i = 0; i < numOfPlayers; i++) {
          var playerVote =  Math.round(Math.random());
          $('.players ul').append('<li class="vote-' + playerVote +'"><div class="left"><img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/Octagonal_pyramid1.png" class="pic"/></div><div class="right"><h3>Name</h3><span class="player-qli">QLI</span></div></li>');
          // $('.players ul li').css('width', 1/numOfPlayers * 100+'%');
        }

        $.ajax({
          type: "POST",
          url: "/setup",
          data: JSON.stringify({
            person: {
              race: $('[name=race]').val(),
              education: $('[name=education]').val(),
              employment: $('[name=employment]').val(),
            },

            // user config for the world
            world: _.extend({
              n_buildings: rows * cols,
              max_tenants: max_tenants,
            }, config)
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
          url: "/step",
          success: function() {
            $('.step-simulation').hide();
          }
        })
      });

      socket.on("setup", function(data){
        var config = {
          maxTenants: max_tenants
        }
        sim.setup(rows, cols, 0.5, data.population, data.buildings, config);
        sim.start();
      });

      socket.on("simulation", function(data){
        // simulation step finished
        if (data.success) {
          $('.step-simulation').show();
        }
      });

      // Whenever players join
      var i = 2;
      socket.on("joined", function(data){
        console.log(i);
        // Adding players to the bottom section
        $('.players-joining ul li.template').clone().appendTo('.players-joining ul').removeClass("template");
        $('.players-joining ul li:nth-child(' + i + ') h3.name').text(data.name);
        i++;
      });

      socket.on("left", function(data){
        console.log(data.name);
      });

      socket.on("twooter", function(data){
        // don't twoot everything, it's too much
        if (Math.random() < 0.2) {
          data.username = slugify(data.name);
          $(".twooter-feed").prepend(renderTemplate('twoot', data));
        }
      });

      socket.on("person", function(data){
        var person = sim.city.getPerson(data.id);
        if (!person) {
          return;
        }
        if (data.event === 'fired') {
          person.status('unemployed');
          sim.city.blink(person.mesh);
        } else if (data.event === 'hired') {
          person.status('employed');
          sim.city.blink(person.mesh);
        } else if (data.event === 'started_firm') {
          person.status('owner');
          sim.city.blink(person.mesh);
        } else if (data.event === 'died') {
          sim.city.die(person);
        }
      });

      socket.on("buildings", function(data){
        var id = data.id,
            building = sim.city.buildings[id];
        if (data.event === 'added_tenant') {
          building.add(data.tenant);
        } else if (data.event === 'removed_tenant') {
          var tenant = building.getTenant(data.tenant.id);
          if (tenant) {
            building.remove(tenant);
          }
        }
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
