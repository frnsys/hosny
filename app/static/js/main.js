require([
  'simulation'
], function(Simulation) {
  var sim = new Simulation(),
      players = [],
      queued_players = [],
      rows = 6,
      cols = 6,
      max_tenants = 10,
      socket = io('/simulation'),
      config = {
        patient_zero_prob: 0.01,
        contact_rate: 0.2,
        transmission_rate: 0.1, // same as below
        sickness_severity: 0.01, // 10 = Aggressive strain of rare virus? | 0.1 = Everyone is super healthy, no one ever gets sick. Like ever.
        recovery_prob: 0.8,
        tax_rate: 0.3,
        tax_rate_increment: 0,
        welfare_increment: 0,
        welfare: 10,
        consumer_good_utility: 1, // 10 = There a super food that is really affordable and filling? | 0.1 = A blight leaves us with just expensive corn.
        rent: 1000,
        labor_cost_per_good: 2,
        material_cost_per_good: 2,
        labor_per_worker: 50, // 10 = Everyone is extremely hard working | 0.1 = The entire population is demotivated to contribute to society
        labor_per_equipment: 50, // 10 = Super automated tech | 0.1 = We go back to rock tools
        supply_increment: 10,
        profit_increment: 10,
        wage_increment: 1,
        extravagant_wage_range: 100,
        residence_size_limit: 100,
        base_min_consumption: 0,
        wage_under_market_multiplier: 1,
        min_business_capital: 75000,
        starting_wage: 5,
        desiredWage: 5,
        starting_welfare_req: 10000
      };

  console.log(config);

require([
  'graph'
], function(Graph) {

  $(function() {
    var socket = io('/simulation'),
        graphs = {
          mean_quality_of_life: new Graph(".graphs-qli", "mean_quality_of_life", 350, 100, "", false),
          mean_healthcare_price: new Graph(".graphs-healthcare", "mean_healthcare_price", 350, 100, "", false),
          mean_cash: new Graph(".graphs-cash", "mean_cash", 350, 100, "", false),
          n_sick: new Graph(".graphs-sick", "n_sick", 350, 100, "", false),
          mean_consumer_good_profit: new Graph(".graphs-consumer-good-profit", "mean_consumer_good_profit", 350, 100, "", false),
          mean_wage: new Graph(".graphs-wage", "mean_wage", 350, 100, "", false)
        };

    socket.on("graph", function(data){
      if (data.graph in graphs) {
        var graph = graphs[data.graph];
        graph.update(data.data);
      }
    });
  });
});


  $(function() {
      // have form already, next submits that form
      $(".next").on("click", function(ev) {
        ev.preventDefault();
        var consumer_good_utility, consumer_good_utility_translation, labor_per_equipment, labor_per_equipment_translation, sickness_severity, sickness_severity_translation, transmission_rate, transmission_rate_translation;

        switch ($('[name=good_utility]:checked').val()) {
          case "1":
            consumer_good_utility = 10;
            consumer_good_utility_translation = "Outstanding";
            break;
          case "2":
            consumer_good_utility = 1;
            consumer_good_utility_translation = "Average";
            break;
          case "3":
            consumer_good_utility = 0.2;
            consumer_good_utility_translation = "Poor";
            break;
        }

        switch ($('[name=per_equipment]:checked').val()) {
          case "1":
            labor_per_equipment = 200;
            labor_per_equipment_translation = "Extremely automated";
            break;
          case "2":
            labor_per_equipment = 50;
            labor_per_equipment_translation = "As it is now";
            break;
          case "3":
            labor_per_equipment = 5;
            labor_per_equipment_translation = "Labor intensive";
            break;
        }

        switch ($('[name=disease]:checked').val()) {
          case "1":
            $('.graphs-sick').removeClass('hide').addClass('show');
            $('.graphs-healthcare').removeClass('hide').addClass('show');
            sickness_severity = 0.3;
            transmission_rate = 0.7;
            patient_zero_prob = 0.2;
            recovery_prob = 0.3;
            break;
          case "2":
            sickness_severity = 0.01;
            transmission_rate = 0.1;
            patient_zero_prob = 0.01;
            recovery_prob = 0.8;
            break;
          case "3":
            sickness_severity = 0;
            transmission_rate = 0;
            patient_zero_prob = 0;
            recovery_prob = 1;
            break;
        }

        $.ajax({
          type: "POST",
          url: "/setup",
          data: JSON.stringify({
            // user config for the world
            world: _.extend({
              n_buildings: rows * cols,
              max_tenants: max_tenants
            }, config, {
              consumer_good_utility: consumer_good_utility,
              labor_per_equipment: labor_per_equipment,
              sickness_severity: sickness_severity,
              transmission_rate: transmission_rate,
              patient_zero_prob: patient_zero_prob,
              recovery_prob: recovery_prob
            })
          }),
          contentType: "application/json",
          success: function(data, textStatus, jqXHR) {
            $('.overlay').fadeOut();
            $('.omni').fadeIn();
            $('.step-simulation').show();
            $('.voting .consumer_good_utility').empty().text(consumer_good_utility + " " + consumer_good_utility_translation);
            $('.voting .labor_per_equipment').empty().text(labor_per_equipment + " " + labor_per_equipment_translation);
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
            $('.voting').hide();

            // flush
            $('.marquee .twoot').remove();
          }
        })
      });

      socket.on("setup", function(data){
        var config = {
          maxTenants: max_tenants
        }
        sim.setup(rows, cols, 0.5, data.population, data.buildings, config);
        sim.start();

        // if this is an existing simulation, hide the setup
        if (data.existing) {
          $('.overlay').fadeOut();
          $('.omni').fadeIn();
          players = data.players;
          update_players();
        }
      });

      socket.on("init", function(data){
        queued_players = data.queued_players;
        update_start_players();
      });

      socket.on("simulation", function(data){
        // simulation step finished
        if (data.success) {
          $('.step-simulation').show();
        }
      });

      function update_players() {
        $(".n-players").text(players.length.toString() + " players");
      }

      // Whenever players join
      var i = 2;
      socket.on("joined", function(data){
        players.push(data);
        // Adding players to the bottom section
        $('.players-joining ul li.template').clone().appendTo('.players-joining ul').removeClass("template");
        $('.players ul li.template').clone().appendTo('.players ul').removeClass("template");
        $('.players-joining ul li:nth-child(' + i + ') h3.name').text(data.name);
        $('.players ul li:nth-child(' + i + ') h3.name').text(data.name);
        i++;
        $(".n-players").text("Population of " + players.length.toString());
        update_players();
      });

      socket.on("left", function(data){
        var player = _.findWhere(players, {id: data.id});
        players = _.without(players, player);
        update_players();
      });

      function update_start_players() {
        if (queued_players.length >= 3) {
          $('.start-simulation').show();
          $('.start-queue').text('Ready to start!');
        } else {
          $('.start-simulation').hide();
          if (queued_players.length == 0) {
            $('.start-queue').text('Looking for at least 3 citizens to start...');
          } else {
            $('.start-queue').text('Looking for ' + (3 - queued_players.length).toString() + ' more citizens to start...');
          }
        }
      }

      socket.on("joined_queue", function(data) {
        queued_players.push(data.id);
        update_start_players();
      });

      socket.on("left_queue", function(data) {
        queued_players = _.without(queued_players, data.id);
        update_start_players();
      });

      socket.on("datetime", function(data) {
        $(".datetime").text(data.month.toString() + "/" + data.day.toString() + "/" + data.year.toString());
      });

      var offset = 0,
          step = 4;
      var i = setInterval(function() {
        $('.marquee').css({ textIndent: '-=' + step.toString() + 'px' });
        offset += step;

        //var w = $('.marquee').width(),
            //t = parseInt($('.marquee').css('text-indent'));
        //$('.marquee .twoot').each(function() {
          //if (parseInt($(this).css('text-indent')) + offset + t <= 0) {
            //$(this).remove();
          //}
        //});

      }, 1000/30);

      socket.on("twooter", function(data){
        // don't twoot everything, it's too much
        if (Math.random() < 0.2) {
          data.username = slugify(data.name);
          var t = $(renderTemplate('twoot', data));
          t.css({ textIndent: offset.toString() + 'px' });
          $(".marquee").append(t);
          offset = 0;
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

      socket.on("voting", function(data) {
        $(".voting").show();
        $('.votes, .status').empty();
        console.log(data.proposal);
        $('.proposal').empty().html(renderTemplate('voting', data.proposal));
      });

      socket.on("government", function(data) {
        $('.government').html(renderTemplate('government', data));
      });

      socket.on("votes", function(data) {
        $('.votes').html(data.yays.toString() + " yay, " + data.nays.toString() + " nay");
      });

      socket.on("voted", function(data) {
        var status = data.passed ? "PASSED!" : "FAILED!";
        $('.status').html(status);
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
