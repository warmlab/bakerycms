const DB_STORE_NAME = "shop_cart";
const DB_VERSION = 1;
const TABLE_NAME = "product";
var mycart = {};
var db;

var clicked_obj;
var product_amount = 0;

//indexedDB = window.indexedDB || window.mozIndexedDB || window.webkitIndexedDB || window.msIndexedDB;
var req = indexedDB.open(DB_STORE_NAME, DB_VERSION);
req.onerror = function(e) {
    alert("do not support indexdb " + e.target.errorCode);
};
req.onsuccess = function(e) {
    db = e.target.result;
    console.log("init db done!!!");

    init_product();
};
req.onupgradeneeded = function(e) {
    console.log("init DB onupgradeneeded");
    var store = e.currentTarget.result.createObjectStore(
        TABLE_NAME, {keyPath: ['code', 'spec'], indexNames: ["amount", "image"]}
    );

    store.createIndex('name', 'name', {unique: false});
    store.createIndex('image', 'image', {unique: false});
    store.createIndex('price', 'price', {unique: false});
    store.createIndex('amount', 'amount', {unique: false});
};

function update_product(p, amount) {
    if (!db) {
        console.error("product indexeddb was not initialized");
        return;
    }

    console.log("begin to add product", p);
    var transaction = db.transaction(TABLE_NAME, "readwrite");
    var objectStore = transaction.objectStore(TABLE_NAME);
    var request = objectStore.put(p);
    request.onsuccess = function(e) {
        console.debug("add product successful");
        product_amount += amount;
        update_product_amount();
    };
    request.onerror = function(e) {
        console.error("add product error", this.error);
    };
}

function delete_product(code) {
    if (!db) {
        console.error("product indexeddb was not initialized");
        return;
    }

    console.log("begin to delete product", code);
    var transaction = db.transaction(TABLE_NAME, "readwrite");
    var objectStore = transaction.objectStore(TABLE_NAME);
    var request = objectStore.delete(code);
    request.onsuccess = function(e) {
        console.debug("delete product successful");
        product_amount--;
    };
    request.onerror = function(e) {
        console.error("delete product error", this.error);
    };

    update_product_amount();
}

function init_product() {
    var transaction = db.transaction(TABLE_NAME, "readonly");
    var store = transaction.objectStore(TABLE_NAME);
    var req = store.count();
    product_amount = 0;
    req.onsuccess = function(e) {
        console.log("There are " + e.target.result + " records in db");
    };

    req.onerror = function(e) {
        console.error("display error", this.error);
    };

    store.openCursor().onsuccess = function(e) {
        var cursor = e.target.result;
        if (cursor) {
            console.log("cursor.value", cursor.value);
            if (mycart.products === undefined) {
                mycart.products = [cursor.value];
            } else {
                mycart.products.push(cursor.value);
            }
            product_amount += cursor.value.amount;

            cursor.continue();
        }

        update_product_amount();
    };
}

function display_db() {
    var transaction = db.transaction(TABLE_NAME, "readonly");
    var store = transaction.objectStore(TABLE_NAME);
    var req = store.count();
    req.onsuccess = function(e) {
        console.log("There are " + e.target.result + " records in db");
    };

    req.onerror = function(e) {
        console.error("display error", this.error);
    };

    store.openCursor().onsuccess = function(e) {
        var cursor = e.target.result;
        if (cursor) {
            console.log("cursor.value", cursor.value);
            cursor.continue();
        } else {
            console.log("no more product");
        }
    };
}

function print_cart () {
    mycart.products.forEach(function(element) {
        console.log(element.name, element.amount);
    }, this);
}

function update_product_amount() {
    if (product_amount === 0)
        $("#product-amount").hide();
    else {
        $("#product-amount").show();
        $("#product-amount").html(product_amount);
    }
}

var add_to_card = function(e) {
    var clicked_obj = $(this);
    var original_price = parseFloat($(this).data('price'));
    //$("#pre-cart-title").html("￥" + original_price);
    var $size_buttons = $('#size-buttons');
    if ($(this).data('spec') === undefined) {
        add_product_to_card.call(clicked_obj, $(this));
        return;
    }
    // get size info from server
    $.get('/product/parameters/'+clicked_obj.data('code'), function(data, status) {
        if (status != 'success')
            return;

        console.log('parameter from server', data);

        $size_buttons.html('');
        for (var i in data) {
            if (data[i].id == clicked_obj.data('spec')) {
                $size_buttons.append($('<div class="ui toggle brown button" data-price="'+ data[i].price+'" data-spec="'+data[i].id+'">'+data[i].name+'</div>'))
                console.log(clicked_obj.data('code'));
                $("#pre-cart-title").html("￥" + (parseFloat(clicked_obj.data('price')) + data[i].price));
                $('#pre-cart-title').data("code", clicked_obj.data('code'));
                $('#pre-cart-title').data("name", clicked_obj.data('name'));
                $('#pre-cart-title').data("price", clicked_obj.data('price'));
                $('#pre-cart-image').data("src", clicked_obj.data('image'));

                var size = show_cake_info(data[i].id);
                $("#pre-cart-image").attr("src", "/static/img/" + size + ".jpg");
                //console.log($('#pre-cart-title').data('code'));
            } else
                $size_buttons.append($('<div class="ui basic toggle button" data-price="'+ data[i].price+'" data-spec="'+data[i].id+'">'+data[i].name+'</div>'))
        }

        $('#size-buttons').children().on("click", function(e) {
            $('#size-buttons').children().removeClass("brown").addClass('basic')
            //$(this).state({});
            $(this).addClass('brown').removeClass('basic');
            $("#pre-cart-title").html("￥" + (parseFloat($(this).data('price')) + original_price));
            $('#pre-cart-title').data('code', clicked_obj.data('code'));
            $('#pre-cart-title').data('name', clicked_obj.data('name'));
            $('#pre-cart-title').data('price', clicked_obj.data('price'));
            $('#pre-cart-image').data('src', clicked_obj.data('image'));

            var size = show_cake_info($(this).data('spec'));
            $("#pre-cart-image").attr("src", "/static/img/" + size + ".jpg");
            // need to modify the information about size/person numbers/order time
        });
    });

    //$children.addClass('basic').removeClass('brown');
    //$children.find('div[text=' + $(this).data('spec') + ']').addClass('brown').removeClass('basic');
    //$('#pre-cart').data('code', $(this).data('code'));
    //$('#pre-cart').data('price', $(this).data('price'));
    //$('#pre-cart').data('name', $(this).data('name'));
    $("#pre-cart").modal('show');
};

$("span.addtocart").on('click', add_to_card);
$("div.add-cart-button").on('click', add_to_card);

var update_amount_fn = function($parent, amount) {
    var code = $parent.data('code');
    var spec = $parent.data('spec');
    console.log(code);
    var $amount_label = $parent.find('div.label');
    for(var i=0; i<mycart.products.length; i++) {
        var element = mycart.products[i];
        if (element.code === code && element.spec === spec) {
            if (element.amount + amount < 1)
                break;
            element.amount += amount;
            update_product(element, amount);
            $amount_label.html('<i class="cube icon"></i>' + element.amount);
            break;
        }
    }
};

$(".my-fixed-cart").on('click', function(e) {
    // add content to cart
    var $cart_list = $('#cart-form');
    if (mycart.products === undefined || mycart.products.length === 0) {
        $cart_list.html('<image class="image" src="/static/img/cartempty.png"><div class="description">您的购物车里还没有美食</div>');
        $('#pay-action').hide();
    } else {
        $cart_list.html('');
        mycart.products.forEach(function(p) {
            var $product_detail = '<div class="ui divided list">\
                <div class="item">\
                    <input type="hidden" name="product" value="' + p.code +',' + p.spec + ',' + p.amount + '">\
                    <div class="ui tiny image"><img src="' + p.image +'"></div>\
                    <div class="content" data-code="' + p.code +'" data-spec="'+ p.spec +'" data-name="' + p.name + '">';
            if (p.checked)
                $product_detail += '<a class="header"><i class="checkmark box icon"></i>'+p.name+'</a>';
            else
                $product_detail += '<a class="header"><i class="square outline icon"></i>'+p.name+'</a>';
            $product_detail += '<div class="meta">\
                            <span class="price">￥' + p.price;
            if (p.spec_name)
                $product_detail += '/' + p.spec_name + '<span>';
            $product_detail += '</div>\
                        <div class="extra">\
                            <div class="ui mini labeled action input" data-code="' + p.code +'" data-spec="'+ p.spec +'">\
                                <div class="ui label"><i class="cube icon"></i>' + p.amount +'</div>\
                                <div class="ui mini negative icon button">\
                                    <i class="minus icon"></i></div>\
                                <div class="ui mini positive icon button">\
                                    <i class="plus icon"></i></div>\
                            </div>\
                        </div>\
                    </div>\
                </div>\
            </div>';
            $cart_list.append($product_detail);
        }, this);
        $cart_list.find('a.header').on('click', function(e) {
            var $parent = $(this).parent();
            var code = $parent.data('code');
            var spec = $parent.data('spec');
            var name = $parent.data('name');
            console.log($parent.data('code'), $parent.data('spec'));

            for(var i=0; i<mycart.products.length; i++) {
                var element = mycart.products[i];
                if (element.code === code && element.spec === spec) {
                    element.checked = !element.checked;
                    update_product(element, 0);
                    if (element.checked)
                        $(this).html('<i class="checkmark box icon"></i>'+ name);
                    else
                        $(this).html('<i class="square outline icon"></i>'+ name);
                    break;
                }
            }

            e.preventDefault();
        });
        $('.ui.mini.negative.icon.button').on('click', function(e) {
            update_amount_fn($(this).parent(), -1);; 
        });
        $('.ui.mini.positive.icon.button').on('click', function(e) {
            update_amount_fn($(this).parent(), 1);; 
        });
        $('#pay-action').show();
    }

    $('#shop-cart').modal('show');
});

var add_product_to_card = function($target) {
    $('#pre-cart').modal('hide');
    $('.my-fixed-cart').animate({bottom: '3em'}, 200, 'swing', function() {
        $('.my-fixed-cart').animate({bottom: '3.5em'}, 100, 'swing', function() {
            $('.my-fixed-cart').animate({bottom: '3.3em'}, 100, 'swing');
        });
    });

    var $selected_size = $('#size-buttons > .brown');

    console.log($target);
    var $pre_obj = $target;

    var p = {};
    p.checked = true;
    p.code = $pre_obj.data('code');
    p.name = $pre_obj.data('name');
    console.log($pre_obj.data('src'));
    if ($pre_obj.data('src') !== undefined)
        p.image = $pre_obj.data('src');
    else
        p.image = $('#pre-cart-image').data('src');
    if ($selected_size === undefined || $selected_size.length === 0) {
        p.price = parseFloat($pre_obj.data("price"));
        p.spec = '[]';
    } else {
        p.price = parseFloat($selected_size.data("price")) + parseFloat($pre_obj.data("price"));
        p.spec = $selected_size.data('spec');
        p.spec_name = $selected_size.html();
    }
    p.amount = 1;
    console.log('add the following product to cart', p);
    if (mycart.products === undefined) {
        mycart.products = [p];
        update_product(p, 1);
    } else {
        var added = false;
        for(var i=0; i<mycart.products.length; i++) {
            var element = mycart.products[i];
            console.log("my cart product", element.name);
            if (element.code === p.code && element.spec === p.spec) {
                element.amount++;
                added = true;
                element.checked = true;
                update_product(element, 1);
                break;
            }
        }

        if (!added) {
            console.log("begin to add new product", p.name);
            mycart.products.push(p);
            update_product(p, 1);
        }
    }

    //print_cart();
    display_db();
};
$('#pre-add-to-cart').on('click', function() {add_product_to_card($('#pre-cart-title'))});

//$('#pay-action-button').on('click', function(e) {
//    console.log(e);
//    //console.log($('#cart-form').submit());
//    //e.preventDefault();
//    console.log("{{url_for('.checkout', _external=True)|weixin_authorize('snsapi_userinfo')|safe}}");
//    //location.href="{{url_for('.checkout', _external=True)|weixin_authorize('snsapi_userinfo')|safe}}";
//});

var carousel = function() {
    var $banners = $('#banner > a');
    var $banner_items = $('#banner-item > span');
    var $cur_banner = $banners.first();
    var $cur_banner_item = $banner_items.first();
    var $next_banner, $next_banner_item;
    $banners.hide();
    $cur_banner.show();
    $cur_banner_item.addClass('banner-item-active');

    console.log($banner_items);
    var carousel_fn = function() {
        $next_banner = $cur_banner.next();
        $next_banner_item = $cur_banner_item.next();
        if ($next_banner.length === 0 || $next_banner_item.length === 0) {
            $next_banner = $banners.first();
            $next_banner_item = $banner_items.first();
        }

        $cur_banner.fadeOut(function() {
            $next_banner.fadeIn();
            $cur_banner_item.removeClass('banner-item-active');
            $next_banner_item.addClass('banner-item-active');
            $cur_banner = $next_banner;
            $cur_banner_item = $next_banner_item;
        });
    };
    var carousel_interval = setInterval(carousel_fn, 5000);

    $banner_items.on('click', function(e) {
        var index = parseInt($(this).data('index'));
        clearInterval(carousel_interval);
        $cur_banner.hide();
        $cur_banner_item.removeClass('banner-item-active');
        $cur_banner = $banners.first();
        while (index) {
            $cur_banner = $cur_banner.next();
            index--;
        }
        //$cur_banner = $banners.indexof(index);
        $cur_banner_item = $(this);
        $cur_banner.show();
        $cur_banner_item.addClass('banner-item-active');

        carousel_interval = setInterval(carousel_fn, 5000);
    });
};
