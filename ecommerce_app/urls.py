from django.urls import path


from .views import AddCartView, AdminOrderView, CartItemDetailView, CategoryDetailView, CategoryListView, CustomEmailView, CustomerProductDetailView, CustomerProductListView, CustomerRegistrationView, AdminRegistrationView, LoginView, OrderHistoryView,PasswordResetRequestView, PasswordResetView, PlaceOrderView, ProductDetailView, ProductListView, ProductReviewCreateView, ProductReviewListView, UserDetailView, UserListView, UserProfileUpdateView, WishlistAddProductView, WishlistMoveToCartView, WishlistView

urlpatterns = [
    path('register/customer/', CustomerRegistrationView.as_view(), name='customer-register'),
    path('register/admin/', AdminRegistrationView.as_view(), name='admin-register'),
    path('password_reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('login/', LoginView.as_view(), name='login'),
    path('password-reset/<str:uidb64>/<str:token>/', PasswordResetView.as_view(), name='password-reset'),
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('product_list/', CustomerProductListView.as_view(), name='product-list'),
    path('product_detail/<int:pk>/', CustomerProductDetailView.as_view(), name='product-list'),
    # Add a product to the cart
    path('cart/', AddCartView.as_view(), name='add-to-cart'),
    path('cart_items/<int:pk>/', CartItemDetailView.as_view(), name='cart-item-detail'),
    path('place_order/', PlaceOrderView.as_view(), name='place-order'),
    path('orders/', AdminOrderView.as_view(), name='admin_orders'),
    path('orders/<int:order_id>/', AdminOrderView.as_view(), name='admin_order_detail'),
    path('order_history/', OrderHistoryView.as_view(), name='order_history'),
    path("custom_email/",CustomEmailView.as_view(), name="custom_email"),
    path('profile-update/', UserProfileUpdateView.as_view(), name='user-profile-update'),
    path('wishlist/', WishlistView.as_view(), name='wishlist'),
    path('wishlist/add/', WishlistAddProductView.as_view(), name='wishlist-add-product'),
    path('wishlist/move-to-cart/', WishlistMoveToCartView.as_view(), name='wishlist-move-to-cart'),
    path('reviews/create/', ProductReviewCreateView.as_view(), name='product-review-create'),
    path('reviews/', ProductReviewListView.as_view(), name='product-review-list'),

]