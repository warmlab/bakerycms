/*class Product {
	constructor(code, name, image, price, amount=1) {
		this.code = code;
		this.name = name;
		this.image = image;
		this.price = price;
		this.amount = amount;
	}
}
*/

function Product(code, name, image, price, amount) {
	this.code = code;
	this.name = name;
	this.image = image;
	this.price = price;
	this.amount = amount;
	this.parameters = [];
}

//class Cart {
function Cart(name, type) {
	this._fromJSON = function(json) {
		return JSON.parse(json);
	}

	this.initData = function(json) {
		if (json != null) {
			var data = this._fromJSON(json);
			this.products = data['products'];
		}
	}

	//constructor(name, type) {
	this.prefix = 'bakery-';
	this.name = name;
	this.key = this.prefix + this.name;
	if (type == 'local')
		this.storage = localStorage;
	else
		this.storage = sessionStorage;


	//this.storage.removeItem(this.key);
	var json = this.storage.getItem(this.key);
	this.products = [];
	this.initData(json);
	//}


	this.addProduct = function(product) {
		var added = false;
		for (var p of this.products) {
			if (p.code == product.code
				&& p.parameters.length() == product.parameters.length()) {
				var same_key_sum = 0;
				for (var key in product.parameters)
					if (p.parameters.indexOf(key))
						same_key_sum++;
				if (same_key_sum == p.parameters.length()) {
					p.amount += product.amount;
					added = true;
				}
			}
		}
		if (!added)
			this.products.push(product);

		// add fly motion to page
		//setTimeout("$('#cart-tip').css('display', 'none')", 3000);
		//$("#cart-tip").css('display', 'show');
		//$("#cart-tip").delay(6000).hide(0);

		this.storeData();
	}

	this.substraceProduct = function(code, amount) {
		for (var i = 0; i < this.products.length; i++) {
			if (this.products[i].code == code) {
				if (this.products[i].amount > amount)
					this.products[i].amount -= amount;
				else
					this.products[i].amount = 1;
				break;
			}
		}

		this.storeData();
	}

	this.removeProduct = function(code) {
		for (var i = 0; i < this.products.length; i++) {
			if (this.products[i].code == code) {
				this.products.splice(i, 1);
				break;
			}
		}

	}

	this.clearProduct = function() {
	}

	this.calTotal = function() {
		var total = 0;
		for (var p of this.products) {
			total += p.price * p.amount;
		}

		return total;
	}

	this.storeData = function() {
		var dic = {'products': this.products, 'total': this.calTotal()};
		var json = JSON.stringify(dic);
		this.storage.setItem(this.key, json);
	}
}

$(document).ready(function(){
	var cart = new Cart('cart');
	$(".add-to-cart").click(function(){
		var product = new Product($(this).data("code"),
							  $(this).data("name"),
							  $(this).data("image"),
							  $(this).data("price"));

		cart.addProduct(product);
	});
//product = new Product('003', '美式', '/image', 10, 20);
//cart.addProduct(product);
//cart.removeProduct('002');
});
