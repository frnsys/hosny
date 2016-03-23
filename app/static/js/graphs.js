require([
  'graph'
], function(Graph) {

  $(function() {
    var socket = io('/simulation'),
        graphs = {
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
  });
});
