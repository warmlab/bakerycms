def is_attribute_checked(key, items, param):
    #print(key, items, param)
    for item in items:
        try:
            attr = getattr(item, param)
            #print(item, attr, int(key) == int(attr))
            if int(key) == attr:
                return True
        except Exception as e:
            return False

    return False

def is_image_field(item):
    pass

def init_my_templates(app):
    app.add_template_global(is_attribute_checked, 'is_attribute_checked')
