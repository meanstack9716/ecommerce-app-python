from flask import Blueprint, request, jsonify
from app.models.products import Products
from app.models import User
from app.models.product_review import ProductReview
from app.utils.utils import create_error_response
from constants import PRODUCT_REVIEW_API, GET_PRODUCT_REVIEW_BY_ID_API
from bson import ObjectId
from mongoengine.errors import DoesNotExist, ValidationError
from app.utils.image_upload import validate_fields, upload_image
from flask_jwt_extended import jwt_required, get_jwt_identity

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route(PRODUCT_REVIEW_API, methods=['POST'])
@jwt_required()
def create_review():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()

    if not user:
        return create_error_response({"user": "User not found"}, 404)

    data = request.form
    required_fields = ['product_id', 'rating', 'review']
    is_valid, validation_errors = validate_fields(data, required_fields)

    if not is_valid:
        return create_error_response(validation_errors, 400)

    try:
        try:
            product_id = ObjectId(data['product_id'])
        except (InvalidId, TypeError, ValueError):
            return create_error_response({"error": "The selected product ID is invalid."}, 400)

        product = Products.objects.get(id=product_id)

        existing_review = ProductReview.objects(
            product_id=product_id,
            user_id=user_id
        ).first()

        if existing_review:
            return create_error_response({"error": "You have already reviewed this product."}, 400)

        try:
            rating = int(data['rating'])
        except ValueError:
            return create_error_response({"error": "Rating must be an integer."}, 400)

        if not (1 <= rating <= 5):
            return create_error_response({"error": "Rating must be between 1 and 5."}, 400)

        image = request.files.get('image')
        image_filename = None
        if image:
            image_filename, image_error = upload_image(image)
            if image_error:
                return create_error_response({"error": image_error}, 400)

        review = ProductReview(
            product_id=product,
            user_id=user,
            rating=rating,
            review=data['review'],
            image_url=image_filename
        )
        review.save()

        return jsonify({
            "message": "Review added successfully.",
            "review_id": str(review.id)
        }), 201

    except DoesNotExist:
        return create_error_response({"error": "Product not found."}, 404)
    except ValidationError as ve:
        return create_error_response({"error": str(ve)}, 400)
    except Exception as e:
        return create_error_response({"error": "Something went wrong. " + str(e)}, 500)


@reviews_bp.route(GET_PRODUCT_REVIEW_BY_ID_API, methods=['GET'])
def get_reviews(product_id):
    try:
        try:
            product_obj_id = ObjectId(product_id)
        except Exception:
            return create_error_response({"error": "Invalid product_id"}, 400)
        reviews = ProductReview.objects(product_id=product_obj_id)
        result = []

        for r in reviews:
            result.append({
                "user_id": str(r.user_id.id),
                "rating": r.rating,
                "review": r.review,
                "created_at": r.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })

        return jsonify(result), 200

    except Exception as e:
        return create_error_response({"error": str(e)}, 400)
