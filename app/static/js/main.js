require([
  'simulation',
  'graph'
], function(Simulation, Graph) {
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

      var graphs = {
        mean_wage: new Graph(".graphs", "mean_wage", 650, 200, "mean wage"),
        mean_equip_price: new Graph(".graphs", "mean_equip_price", 650, 200, "mean equip price"),
        mean_material_price: new Graph(".graphs", "mean_material_price", 650, 200, "mean material price"),
        mean_consumer_good_price: new Graph(".graphs", "mean_consumer_good_price", 650, 200, "mean consumer good price"),
        mean_healthcare_price: new Graph(".graphs", "mean_healthcare_price", 650, 200, "mean healthcare price"),
        mean_equip_profit: new Graph(".graphs", "mean_equip_profit", 650, 200, "mean equip profit"),
        mean_material_profit: new Graph(".graphs", "mean_material_profit", 650, 200, "mean material profit"),
        mean_consumer_good_profit: new Graph(".graphs", "mean_consumer_good_profit", 650, 200, "mean consumer good profit"),
        mean_healthcare_profit: new Graph(".graphs", "mean_healthcare_profit", 650, 200, "mean healthcare profit"),
        mean_quality_of_life: new Graph(".graphs", "mean_quality_of_life", 650, 200, "mean quality of life"),
        mean_cash: new Graph(".graphs", "mean_cash", 650, 200, "mean cash"),
        n_sick: new Graph(".graphs", "n_sick", 650, 200, "n sick"),
        n_deaths: new Graph(".graphs", "n_deaths", 650, 200, "n deaths"),
        n_population: new Graph(".graphs", "n_population", 650, 200, "n population"),
        n_firms: new Graph(".graphs", "n_firms", 650, 200, "n firms"),
        n_bankruptcies: new Graph(".graphs", "n_bankruptcies", 650, 200, "n bankruptcies"),
        welfare: new Graph(".graphs", "welfare", 650, 200, "welfare"),
        tax_rate: new Graph(".graphs", "tax_rate", 650, 200, "tax rate")
      };

      socket.on("graph", function(data){
        if (data.graph in graphs) {
          var graph = graphs[data.graph];
          graph.update(data.data);
        }
      });

      //Advancing from setup screen 1 to screen 2
      // var i = 0;
      // $(".next").on("click", function() {
      //   $("fieldset").eq(i).removeClass("show").addClass("hide");
      //   $("fieldset").eq(i+1).removeClass("hide").addClass("show");
      //   i++;
      // });

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
