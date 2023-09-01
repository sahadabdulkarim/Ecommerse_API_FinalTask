from rest_framework import serializers
from .models import CustomUser, Category, Product, ProductReview, Wishlist
from rest_framework import serializers
from .models import CustomUser, CartItem, OrderItem, Category, Product, Order

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'is_staff')
        extra_kwargs = {'password': {'write_only': True, 'required': True}}

    def create(self, validated_data):
        is_staff = validated_data.get('is_staff', False)
        request = self.context.get('request')

        if request and not request.user.is_staff and is_staff:
            raise serializers.ValidationError("You do not have permission to set 'is_staff' to True during registration.")

        user = CustomUser.objects.create_user(**validated_data)
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PasswordResetSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'is_staff']


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'product_name', 'price']

    def get_product_name(self, obj):
        return obj.product.name

    def get_price(self, obj):
        return obj.product.price


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.SerializerMethodField()
    price_at_order = serializers.DecimalField(max_digits=10, decimal_places=2)
    amount_for_item = serializers.SerializerMethodField()
    def get_amount_for_item(self, obj):
        return obj.price_at_order * obj.quantity
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity','amount_for_item', 'price_at_order']

    def get_product(self, order_item):
        product = order_item.product
        return {
            'name': product.name,
            'price': product.price
        }


class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    user = UserSerializer()

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_amount', 'order_status', 'shipping_address', 'payment_method', 'order_items']

    def create(self, validated_data):
        return Order.objects.create(**validated_data)


from rest_framework import serializers

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'last_name')
        extra_kwargs = {
            'email': {'read_only': True},  # Make email read-only to prevent modification
        }

class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = '__all__'

class WishlistAddProductSerializer(serializers.Serializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

class ProductReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    product_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductReview
        fields = '__all__'

    def get_product_name(self, obj):
        return obj.product.name
