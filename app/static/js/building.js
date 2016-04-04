define([], function() {
  var colors = {
    'Hospital': 0xecb4bf,
    'CapitalEquipmentFirm': 0x47d1d5,
    'ConsumerGoodFirm': 0x4bfffe6,
    'RawMaterialFirm': 0x555555,
    'Residential': 0xffff44,
  };

  var Building = function(x, z, maxTenants, city) {
    this.x = x;
    this.z = z;
    this.tenants = [];
    this.maxTenants = maxTenants;
    this.city = city;
  };

  Building.prototype = {
    add: function(tenant) {
      if (this.tenants.length >= this.maxTenants) {
        return false;
      }
      tenant = new Tenant(tenant.id, tenant.type);

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
          self.city.remove(t.mesh);
      });

      var tenants = _.without(this.tenants, tenant);
      this.tenants = [];

      _.each(tenants, function(t) {
          self.add({
            id: t.id,
            type: t.type
          });
      });
    },

    getTenant: function(id) {
      return _.find(this.tenants, function(t) {
        return t.id === id;
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

  var Tenant = function(id, type) {
    var side = 1,
        height = 0.5,
        color = colors[type],
        geometry = new THREE.BoxGeometry(side, height, side),
        material = new THREE.MeshLambertMaterial({
          color: color
        });
    this.mesh = new THREE.Mesh(geometry, material);
    this.id = id;
    this.type = type;
  }

  return Building;
});
