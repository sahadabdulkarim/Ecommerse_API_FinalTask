from rest_framework import generics, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model, authenticate
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.core.mail import send_mail
from .models import Coupon, CustomUser, Product, Category, CartItem, Order, OrderItem,Cart, ProductReview, Wishlist
from .serializers import (
    CouponSerializer, CustomUserSerializer, PasswordResetRequestSerializer,
    LoginSerializer, PasswordResetSerializer, ProductReviewSerializer, ProductSerializer,
    CategorySerializer, UserProfileUpdateSerializer, UserSerializer, CartItemSerializer,
    OrderSerializer, WishlistAddProductSerializer, WishlistSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from .permissions import IsCartOwner, IsSuperuserOrAdmin
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

# Create your views here.
class CustomerRegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            user = response.data
            email = user['email']
            subject = 'Welcome to our Website!'
            html_message = render_to_string('ecommerce_app/welcome_email.html')
            plain_message = strip_tags(html_message)
            send_mail(subject, plain_message, 'noreply@yourwebsite.com', [email], html_message=html_message)
        return response

class AdminRegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [IsSuperuserOrAdmin]

    def create(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({'error': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)
    

class PasswordResetRequestView(generics.CreateAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        self.send_password_reset_email(email)
        return Response({'success': 'If an account with this email exists, you will receive an email with further instructions.'}, status=status.HTTP_200_OK)
    
    def send_password_reset_email(self, email):
        User = get_user_model()
        user = User.objects.filter(email=email).first()
        
        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"http://localhost:8000/password-reset/{uid}/{token}/"
            
            subject = 'Password Reset Request'
            html_message = render_to_string('ecommerce_app/password_reset.html', {'reset_url': reset_url})
            plain_message = strip_tags(html_message)
            
            from_email = 'noreply@yourwebsite.com'
            recipient_list = [email]
            
            send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(email=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            return Response({'access_token': access_token, 'refresh_token': refresh_token}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class PasswordResetView(generics.CreateAPIView):
    serializer_class = PasswordResetSerializer

    def post(self, request, uidb64, token):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data['new_password']

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            User = get_user_model()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response({'success': 'Password reset successful.'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)

class ProductListView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = PageNumberPagination

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]

class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAdminUser]

class UserListView(generics.ListCreateAPIView):
    queryset = CustomUser.objects.filter(is_staff=False)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = PageNumberPagination

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CustomUser.objects.filter(is_staff=False)
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

class CustomerProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        queryset = Product.objects.all()

        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category__id=category_id)

        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price and max_price:
            queryset = queryset.filter(price__gte=min_price, price__lte=max_price)

        product_name = self.request.query_params.get('name')
        if product_name:
            queryset = queryset.filter(name__icontains=product_name)

        return queryset

class CustomerProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

class AddCartView(generics.CreateAPIView, generics.ListAPIView):
    queryset = Product.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = CartItemSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        user = self.request.user
        return CartItem.objects.filter(cart__user=user)
    def post(self, request, *args, **kwargs):
        user = request.user
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity')

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({"message": "Product not found"}, status=status.HTTP_400_BAD_REQUEST)
        cart, created = Cart.objects.get_or_create(user=user)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

        if not created:
            cart_item.quantity += quantity  
        else:
            cart_item.quantity = quantity

        if cart_item.quantity > product.quantity:
            return Response({"message": "Requested quantity exceeds available quantity"}, status=status.HTTP_400_BAD_REQUEST)

        cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated, IsCartOwner]

# class PlaceOrderView(generics.CreateAPIView):
#     queryset = Order.objects.all()
#     serializer_class = OrderSerializer
#     permission_classes = [IsAuthenticated, IsCartOwner]

#     def create(self, request, *args, **kwargs):
#         user = request.user
#         cart_items = CartItem.objects.filter(cart__user=user)

#         if not cart_items:
#             return Response({"message": "No cart items found"}, status=status.HTTP_400_BAD_REQUEST)

#         total_amount = 0
#         order_items = []

#         for cart_item in cart_items:
#             item_amount = cart_item.product.price * cart_item.quantity
#             total_amount += cart_item.product.price * cart_item.quantity
#             order_items.append({
#                 "product": cart_item.product,
#                 "quantity": cart_item.quantity,
#                 "price_at_order": cart_item.product.price,
#                 "amount": item_amount,
#             })

#         shipping_address = request.data.get("shipping_address")
#         payment_method = request.data.get("payment_method")

#         order = Order.objects.create(
#             user=user,
#             total_amount=total_amount,
#             shipping_address=shipping_address,
#             payment_method=payment_method,
#         )

#         for item in order_items:
#             product = item['product']
#             quantity = item['quantity']
#             price_at_order = item['price_at_order']
#             product.quantity -= quantity
#             product.save()

#             OrderItem.objects.create(order=order, product=product, quantity=quantity,price_at_order=price_at_order)

#             cart_item = CartItem.objects.get(cart__user=user, product=product)
#             cart_item.delete()

#         user_subject = 'Order Confirmation'
#         user_message = render_to_string('ecommerce_app/order_confirmation.html', {
#             'user': user,
#             'order_items': order_items,
#             'order': order,
#         })
#         user_message_plain = strip_tags(user_message)
#         send_mail(user_subject, user_message_plain, 'your-email@example.com', [user.email], html_message=user_message)

#         admin_subject = 'New Order'
#         admin_message = f"A new order has been placed. Order ID: {order.id}"
#         send_mail(admin_subject, admin_message, 'your-email@example.com', ['admin-email@example.com'])

#         serializer = self.get_serializer(order)

#         return Response(serializer.data, status=status.HTTP_201_CREATED)

class AdminOrderView(APIView):
    permission_classes = [permissions.IsAdminUser]
    pagination_class = PageNumberPagination

    def get(self, request,order_id):
        try:
            order = Order.objects.get(id=order_id)
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response({'message': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, order_id):
        order = Order.objects.get(id=order_id)
        order_status = request.data.get('order_status')

        if order_status:
            order.order_status = order_status
            order.save()
            return Response({'message': 'Order status updated successfully.'})
        else:
            return Response({'message': 'Please provide the order_status field.'})

class OrderHistoryView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(user=user)
    


class CustomEmailView(APIView):
    permission_classes = [IsAuthenticated,permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        subject = request.data.get('subject')
        message = request.data.get('message')
        recipients = CustomUser.objects.filter(is_staff=False, email__isnull=False)
        files = request.FILES.getlist('files')
        if not subject or not message or not recipients:
            return Response({'message': 'Subject, message, and recipient(s) are required.'}, status=status.HTTP_400_BAD_REQUEST)

        context = {'subject': subject, 'message': message,"files":files}
        html_message = render_to_string('ecommerce_app/custom_email.html', context)

        email = EmailMultiAlternatives(
            subject=subject,
            body=html_message,  
            from_email='noreply@yourwebsite.com',
            to=[user.email for user in recipients],
        )
        for file in files:
            email.attach(file.name, file.read(), file.content_type)
        email.content_subtype = 'html'

        
        try:
            email.send()
            return Response({'message': 'Custom email sent successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            # Log the error for debugging
            print(e)
            return Response({'message': 'An error occurred while sending the email.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_password = request.data.get('password', None)

        # Update password if a new one is provided
        if new_password:
            instance.set_password(new_password)
            instance.save()

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)

class WishlistView(generics.RetrieveAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return Wishlist.objects.get_or_create(user=self.request.user)[0]

class WishlistAddProductView(generics.CreateAPIView):
    serializer_class = WishlistAddProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        wishlist = Wishlist.objects.get_or_create(user=request.user)[0]
        product_id = request.data.get('product_id')

        try:
            product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({"message": "Product not found"}, status=status.HTTP_400_BAD_REQUEST)

        wishlist.products.add(product)
        return Response({"message": "Product added to wishlist"}, status=status.HTTP_201_CREATED)
    
class WishlistMoveToCartView(generics.CreateAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        wishlist = Wishlist.objects.get_or_create(user=request.user)[0]
        product_id = request.data.get('product_id')

        try:
            product = wishlist.products.get(pk=product_id)
        except Product.DoesNotExist:
            return Response({"message": "Product not found in wishlist"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the product is already in the cart
        if CartItem.objects.filter(cart__user=request.user, product=product).exists():
            return Response({"message": "Product is already in the cart"}, status=status.HTTP_400_BAD_REQUEST)

        # Add the product to the cart
        cart, _ = Cart.objects.get_or_create(user=request.user)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        # Remove the product from the wishlist
        wishlist.products.remove(product)

        return Response({"message": "Product moved from wishlist to cart"}, status=status.HTTP_200_OK)



class ProductReviewCreateView(generics.CreateAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]  # User must be authenticated to leave a review

    def perform_create(self, serializer):
        product_id = self.request.data.get('product')
        user = self.request.user
        purchased_products = OrderItem.objects.filter(order__user=user, product_id=product_id)
        
        if purchased_products.exists():
            serializer.save(user=user)
        else:
            # You can raise a PermissionDenied exception or return an error response
            raise permissions.PermissionDenied("You can only review products that you have purchased.")


class ProductReviewListView(generics.ListAPIView):
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.AllowAny]  # Allow anyone to view reviews

    def get_queryset(self):
        product_id = self.request.query_params.get('product_id')
        if product_id:
            return ProductReview.objects.filter(product_id=product_id)
        return ProductReview.objects.all()


class CreateCouponView(generics.CreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAdminUser]


class ListCouponsView(generics.ListAPIView):
    queryset = Coupon.objects.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now())
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated]

class ValidateCouponForCartView(generics.CreateAPIView):
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated, IsCartOwner]
    def get_object(self):
        coupon_code = self.kwargs['coupon_code']
        try:
            coupon = Coupon.objects.get(coupon_code=coupon_code, start_date__lte=timezone.now(), end_date__gte=timezone.now())
            return coupon
        except Coupon.DoesNotExist:
            return None
    def calculate_discount(self, coupon, cart_items):
        discount_details = {
            'discount_type': coupon.discount_type,
            'discount_value': coupon.discount_value,
            'discount_amount': 0, 
        }
        cart_total = sum(cart_item.product.price * cart_item.quantity for cart_item in cart_items)
        if coupon.discount_type == 'percentage':
        # Calculate discount for percentage type coupon
            if cart_total >= coupon.min_purchase_amount:
                discount_details['discount_amount'] = (coupon.discount_value / 100) * cart_total
                return discount_details

        elif coupon.discount_type == 'amount':
            # Calculate discount for fixed amount type coupon
            if cart_total >= coupon.min_purchase_amount:
                discount_details['discount_amount'] = coupon.discount_value
                return discount_details

        return None  # Return None if the coupon doesn't apply to the cart
    def create(self, request, *args, **kwargs):
        coupon_code = request.data.get('coupon_code', '')  # Get the coupon code from the request body

        if not coupon_code:
            return Response({"message": "Coupon code is required in the request body"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            coupon = Coupon.objects.get(
                coupon_code=coupon_code,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now(),
            )
        except Coupon.DoesNotExist:
            return Response({"message": "Invalid or expired coupon code"}, status=status.HTTP_400_BAD_REQUEST)

        # Get the authenticated user's cart items.
        cart_items = CartItem.objects.filter(cart__user=request.user)

        discount_details = self.calculate_discount(coupon, cart_items)

        if not discount_details:
            return Response({"message": "Coupon does not apply to the cart items"}, status=status.HTTP_400_BAD_REQUEST)
        cart_total = sum(cart_item.product.price * cart_item.quantity for cart_item in cart_items)
        final_price = cart_total - discount_details["discount_amount"]
        response_data = {
            "original_total_amount": cart_total,
            "discount_details": discount_details,
            "final_price": final_price,
        }
        return Response(response_data, status=status.HTTP_200_OK)


class PlaceOrderView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsCartOwner]
    def calculate_discount(self, coupon, cart_items):
        discount_details = {
            'discount_type': coupon.discount_type,
            'discount_value': coupon.discount_value,
            'discount_amount': 0, 
        }
        cart_total = sum(cart_item.product.price * cart_item.quantity for cart_item in cart_items)
        if coupon.discount_type == 'percentage':
        # Calculate discount for percentage type coupon
            if cart_total >= coupon.min_purchase_amount:
                discount_details['discount_amount'] = (coupon.discount_value / 100) * cart_total
                return discount_details

        elif coupon.discount_type == 'amount':
            # Calculate discount for fixed amount type coupon
            if cart_total >= coupon.min_purchase_amount:
                discount_details['discount_amount'] = coupon.discount_value
                return discount_details

        return None  # Return None if the coupon doesn't apply to the cart
    def create(self, request, *args, **kwargs):
        user = request.user
        cart_items = CartItem.objects.filter(cart__user=user)

        if not cart_items:
            return Response({"message": "No cart items found"}, status=status.HTTP_400_BAD_REQUEST)
        # Check if the coupon code has already been applied to any order
        coupon_code = request.data.get("coupon_code")
        if coupon_code and Order.objects.filter(coupon_code=coupon_code, coupon_applied=True).exists():
            return Response({"message": "Coupon has already been used"}, status=status.HTTP_400_BAD_REQUEST)
        # Calculate the total amount for the order without applying the coupon
        total_amount_without_coupon = sum(cart_item.product.price * cart_item.quantity for cart_item in cart_items)

        # Get the coupon code from the request data
        coupon_code = request.data.get("coupon_code")
        # Initialize discount_amount to zero
        discount_amount = 0
        # Apply the coupon discount if a valid coupon code is provided
        if coupon_code:
            try:
                coupon = Coupon.objects.get(
                    coupon_code=coupon_code,
                    start_date__lte=timezone.now(),
                    end_date__gte=timezone.now(),
                )
                
                # Check if the coupon can still be used (max_usage check)
                if coupon.max_usage is not None and coupon.max_usage <= 0:
                    return Response({"message": "Coupon has reached its maximum usage limit"}, status=status.HTTP_400_BAD_REQUEST)

                # Calculate discount details
                discount_details = self.calculate_discount(coupon, cart_items)

                if discount_details:
                    discount_amount = discount_details["discount_amount"]
                    total_amount = total_amount_without_coupon - discount_amount

                    # Decrease the max_usage of the coupon by 1
                    if coupon.max_usage is not None:
                        coupon.max_usage -= 1
                        coupon.save()
                else:
                    return Response({"message": "Coupon does not apply to the cart items"}, status=status.HTTP_400_BAD_REQUEST)
            except Coupon.DoesNotExist:
                return Response({"message": "Invalid or expired coupon code"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            total_amount = total_amount_without_coupon

        shipping_address = request.data.get("shipping_address")
        payment_method = request.data.get("payment_method")

        order = Order.objects.create(
            user=user,
            total_amount_without_coupon=total_amount_without_coupon,
            total_amount=total_amount,
            shipping_address=shipping_address,
            payment_method=payment_method,
            coupon_code=coupon_code,  # Add the coupon code to the order
            discounted_amount=discount_amount,  # Add the discounted amount to the order
        )
        order.coupon_applied = True
        order.save()
        order_items = []
        for cart_item in cart_items:
            product = cart_item.product
            quantity = cart_item.quantity
            price_at_order = product.price
            product.quantity -= quantity
            product.save()

            order_item = OrderItem.objects.create(order=order, product=product, quantity=quantity, price_at_order=price_at_order)
            order_items.append(order_item)
            cart_item.delete()

        user_subject = 'Order Confirmation'
        user_message = render_to_string('ecommerce_app/order_confirmation.html', {
            'user': user,
            'order_items': order_items,
            'order': order,
            'discounted_amount': discount_amount,
        })
        user_message_plain = strip_tags(user_message)
        send_mail(user_subject, user_message_plain, 'your-email@example.com', [user.email], html_message=user_message)

        admin_subject = 'New Order'
        admin_message = f"A new order has been placed. Order ID: {order.id}"
        send_mail(admin_subject, admin_message, 'your-email@example.com', ['admin-email@example.com'])

        serializer = self.get_serializer(order)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
