define([], function() {
  var MAXTENANTS = 10;

  var colors = {
    // TODO diff colors for public vs private
    'Hospital': 0xff2222,
    //'Hospital': 0x44ffff,
    'Business': 0x555555,
    'Residential': 0xffff44,
  };

  var Building = function(x, z, city) {
    this.x = x;
    this.z = z;
    this.tenants = [];
    this.city = city;
  };

  Building.prototype = {
    add: function(tenant) {
      if (this.tenants.length >= MAXTENANTS) {
        return false;
      }
      this.city.place(
        tenant.mesh,
        this.x,
        this.height + tenant.mesh.geometry.parameters.height/2,
        this.z);
      this.tenants.push(tenant);
    },

    remove: function(tenant) {
      // basically just rebuild the building without the removed tenant
      var self = this;
      _.each(this.tenants, function(t) {
          this.city.remove(t.mesh);
      });

      var tenants = _.without(this.tenants, tenant);
      this.tenants = [];

      _.each(tenants, function(t) {
          self.add(t);
      });
    },

    // total height of the building
    get height() {
      return _.reduce(this.tenants, function(mem, t) {
          return mem + t.mesh.geometry.parameters.height;
      }, 0);
    },

    get vacancies() {
      return MAXTENANTS - this.tenants.length;
    }
  }

  var Tenant = function(type) {
    var side = 1,
        height = 0.5,
        color = colors[type],
        geometry = new THREE.BoxGeometry(side, height, side),
        material = new THREE.MeshLambertMaterial({
          color: color
        });
    this.mesh = new THREE.Mesh(geometry, material);
  }

  return {
    Building: Building,
    Tenant: Tenant
  };
});
