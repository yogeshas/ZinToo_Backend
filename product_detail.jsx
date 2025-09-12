"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Navbar from "../../components/Navbar";
import Footer from "../../components/Footer";
import { useEcom } from "../../context/EcomContext";
import { toast, ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import { FaHeart, FaShoppingCart, FaStar, FaWhatsapp, FaFacebook, FaLink } from "react-icons/fa";
import { decryptData, encryptData } from "../../utils/crypto";

// Product interface matching backend
interface Product {
  id: number;
  pname: string;
  pdescription: string;
  price: number;
  final_price?: number;
  original_price?: number;
  image: string;
  images?: string[];
  category?: string;
  subcategory?: string;
  tag?: string;
  is_new?: boolean;
  is_featured?: boolean;
  is_latest?: boolean;
  is_trending?: boolean;
  rating?: number;
  is_cod_available?: boolean;
  sizes?: { [key: string]: number };
  available_sizes?: string[];
  color?: string;
  // New color structure with sizes, counts, and images
  colors?: ProductColor[];
  // Legacy variant structure (keeping for backward compatibility)
  variants?: ProductVariant[];
}

// New color interface for advanced color/size management
interface ProductColor {
  id: number;
  name: string;
  sizes: string[];
  sizeCounts: { [key: string]: number };
  images: string[];
}

// Legacy variant interface (keeping for backward compatibility)
interface ProductVariant {
  id: number;
  color: string;
  color_code?: string;
  size: string;
  stock: number;
  price?: number;
  final_price?: number;
  original_price?: number;
  image?: string;
  images?: string[];
  is_available?: boolean;
}

export default function ProductDetailPage() {
  const params = useParams();
  const productId = params?.id;
  const { isLoggedIn, userToken, cart, wishlist, addToCartBackend, addToWishlistBackend } = useEcom();
  
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedImage, setSelectedImage] = useState(0);
  const [quantity, setQuantity] = useState(1);
  const [selectedSize, setSelectedSize] = useState<string>("");
  const [selectedColor, setSelectedColor] = useState<string>("");
  const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(null);
  const [availableColors, setAvailableColors] = useState<string[]>([]);
  const [availableSizes, setAvailableSizes] = useState<string[]>([]);
  // New state for color-based system
  const [selectedColorData, setSelectedColorData] = useState<ProductColor | null>(null);
  const [currentImages, setCurrentImages] = useState<string[]>([]);
  const [reviewStats, setReviewStats] = useState<any | null>(null);
  const [reviews, setReviews] = useState<any[]>([]);
  const [similarProducts, setSimilarProducts] = useState<Product[]>([]);
  const [newReview, setNewReview] = useState<{ rating: number; title: string; content: string; files: File[] }>({ rating: 5, title: "", content: "", files: [] });
  const [hoverRating, setHoverRating] = useState<number | null>(null);
  const [commentDrafts, setCommentDrafts] = useState<Record<number, string>>({});
  // Media viewer state
  const [viewerOpen, setViewerOpen] = useState(false);
  const [viewerItems, setViewerItems] = useState<Array<{ url: string; type: 'image' | 'video' }>>([]);
  const [viewerIndex, setViewerIndex] = useState(0);
  const [pincode, setPincode] = useState("");
  const [pincodeStatus, setPincodeStatus] = useState<null | { serviceable: boolean; message: string }>(null);
  const [selectedAddressId, setSelectedAddressId] = useState<string>("");
  const [addresses, setAddresses] = useState<any[]>([]);

  // Use S3 URLs directly - no normalization needed
  const normalizeUrl = (u: string): string => {
    return u; // Return URL as-is since it's already a full S3 URL
  };

  // Process colors and extract available colors and sizes
  const processColors = (productData: Product) => {
    if (productData.colors && productData.colors.length > 0) {
      // Extract color names and set first color as default
      const colorNames = productData.colors.map(c => c.name);
      setAvailableColors(colorNames);
      
      // Set first color as default
      const firstColor = productData.colors[0];
      setSelectedColorData(firstColor);
      setSelectedColor(firstColor.name);
      setAvailableSizes(firstColor.sizes);
      setCurrentImages(firstColor.images);
      
      // Set first available size as default
      const firstAvailableSize = firstColor.sizes.find(size => firstColor.sizeCounts[size] > 0);
      if (firstAvailableSize) {
        setSelectedSize(firstAvailableSize);
      }
    } else if (productData.variants && productData.variants.length > 0) {
      // Fallback to variant logic
      const colors = [...new Set(productData.variants.map(v => v.color))];
      const sizes = [...new Set(productData.variants.map(v => v.size))];
      
      setAvailableColors(colors);
      setAvailableSizes(sizes);
      
      // Set first variant as default if available
      const firstAvailableVariant = productData.variants.find(v => v.is_available !== false && v.stock > 0);
      if (firstAvailableVariant) {
        setSelectedVariant(firstAvailableVariant);
        setSelectedColor(firstAvailableVariant.color);
        setSelectedSize(firstAvailableVariant.size);
      }
    } else {
      // Fallback to old logic if no variants
      setAvailableColors(productData.color ? productData.color.split(',').map(c => c.trim()) : []);
      setAvailableSizes(productData.available_sizes || Object.keys(productData.sizes || {}));
      setCurrentImages(productData.images || [productData.image]);
    }
  };

  // Handle color selection with new color structure
  const handleColorSelection = (colorName: string) => {
    if (!product) return;
    
    setSelectedColor(colorName);
    
    if (product.colors && product.colors.length > 0) {
      // Find color data for selected color
      const colorData = product.colors.find(c => c.name === colorName);
      if (colorData) {
        setSelectedColorData(colorData);
        setAvailableSizes(colorData.sizes);
        setCurrentImages(colorData.images);
        
        // Reset selected size and select first available size
        setSelectedSize("");
        const firstAvailableSize = colorData.sizes.find(size => colorData.sizeCounts[size] > 0);
        if (firstAvailableSize) {
          setSelectedSize(firstAvailableSize);
        }
      }
    } else if (product.variants && product.variants.length > 0) {
      // Fallback to variant logic
      let targetVariant = product.variants.find(v => 
        v.color === colorName && v.size === selectedSize && v.is_available !== false && v.stock > 0
      );
      
      // If no variant with current size, find first available size for this color
      if (!targetVariant) {
        targetVariant = product.variants.find(v => 
          v.color === colorName && v.is_available !== false && v.stock > 0
        );
        if (targetVariant) {
          setSelectedSize(targetVariant.size);
        }
      }
      
      setSelectedVariant(targetVariant || null);
    }
  };

  // Handle size selection with new color structure
  const handleSizeSelection = (size: string) => {
    if (!product) return;
    
    setSelectedSize(size);
    
    if (product.colors && product.colors.length > 0) {
      // For new color structure, size selection doesn't change color or images
      // Just update the selected size
      return;
    } else if (product.variants && product.variants.length > 0) {
      // Fallback to variant logic
      let targetVariant = product.variants.find(v => 
        v.size === size && v.color === selectedColor && v.is_available !== false && v.stock > 0
      );
      
      // If no variant with current color, find first available color for this size
      if (!targetVariant) {
        targetVariant = product.variants.find(v => 
          v.size === size && v.is_available !== false && v.stock > 0
        );
        if (targetVariant) {
          setSelectedColor(targetVariant.color);
        }
      }
      
      setSelectedVariant(targetVariant || null);
    }
  };

  // Get available sizes for selected color
  const getAvailableSizesForColor = (color: string) => {
    if (!product?.variants) return availableSizes;
    return product.variants
      .filter(v => v.color === color && v.is_available !== false && v.stock > 0)
      .map(v => v.size);
  };

  // Get available colors for selected size
  const getAvailableColorsForSize = (size: string) => {
    if (!product?.variants) return availableColors;
    return product.variants
      .filter(v => v.size === size && v.is_available !== false && v.stock > 0)
      .map(v => v.color);
  };

  // Fetch product data from backend
  useEffect(() => {
    const fetchProduct = async () => {
      if (!productId) return;
      
      try {
        setLoading(true);
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
        console.log('📡 [PRODUCT] Fetching product with ID:', productId);
        
        const response = await fetch(`${API_URL}/api/products/${productId}`);
        console.log('📡 [PRODUCT] Response status:', response.status);
        
        if (response.ok) {
          const result = await response.json();
          console.log('📡 [PRODUCT] API response:', result);
          
          if (result.success && result.encrypted_data) {
            const decryptedData = decryptData(result.encrypted_data);
            console.log('📡 [PRODUCT] Decrypted product data:', decryptedData);
            
            if (decryptedData && decryptedData.product) {
              const productData = decryptedData.product;
              
              // Fix image URLs - convert relative paths to absolute URLs
              if (productData.image) {
                productData.image = normalizeUrl(productData.image);
              }
              
              if (productData.images && Array.isArray(productData.images)) {
                productData.images = productData.images.map((img: string) => normalizeUrl(img));
              }
              
              setProduct(productData);
              setReviewStats(decryptedData.review_stats || null);
              
              // Process colors and set up color/size selection
              processColors(productData);
              
              // Set first image as selected if images exist
              if (productData.images && productData.images.length > 0) {
                setSelectedImage(0);
              }
            } else {
              setError('Product data not found');
            }
          } else {
            setError('Failed to load product data');
          }
        } else {
          const errorText = await response.text();
          console.error('📡 [PRODUCT] Error response:', errorText);
          setError(`Failed to load product (${response.status})`);
        }
      } catch (error) {
        console.error('📡 [PRODUCT] Error fetching product:', error);
        setError('Network error. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchProduct();
  }, [productId]);

  // Fetch reviews for this product
  const fetchReviews = async () => {
    if (!productId) return;
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
      const res = await fetch(`${API_URL}/api/reviews/product/${productId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.success && data.encrypted_data) {
          const dec = decryptData(data.encrypted_data);
          const list = (dec?.reviews || []).map((r: any) => ({
            ...r,
            images: (r.images || []).map((u: string) => normalizeUrl(u)),
            videos: (r.videos || []).map((u: string) => normalizeUrl(u)),
          }));
          setReviews(list);
          setReviewStats(dec?.stats || null);
        }
      }
    } catch (e) {
      // ignore
    }
  };

  useEffect(() => { fetchReviews(); }, [productId]);

  // Load similar products
  useEffect(() => {
    const loadSimilarProducts = async () => {
      if (!product) return;
      
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
        const response = await fetch(`${API_URL}/api/products?category=${product.category}&limit=8`);
        
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.encrypted_data) {
            const decryptedData = decryptData(data.encrypted_data);
            if (decryptedData && decryptedData.products) {
              // Filter out current product and limit to 8, normalize image URLs
              const similar = decryptedData.products
                .filter((p: Product) => p.id !== product.id)
                .slice(0, 8)
                .map((p: Product) => ({
                  ...p,
                  image: normalizeUrl(p.image),
                  images: p.images ? p.images.map((img: string) => normalizeUrl(img)) : undefined
                }));
              setSimilarProducts(similar);
            }
          }
        }
      } catch (err) {
        console.error('Error loading similar products:', err);
      }
    };

    loadSimilarProducts();
  }, [product]);

  // Keyboard navigation for media viewer
  useEffect(() => {
    if (!viewerOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setViewerOpen(false);
      if (e.key === 'ArrowRight') setViewerIndex((i) => (i + 1) % (viewerItems.length || 1));
      if (e.key === 'ArrowLeft') setViewerIndex((i) => (i - 1 + (viewerItems.length || 1)) % (viewerItems.length || 1));
    };
    window.addEventListener('keydown', onKey as any);
    return () => window.removeEventListener('keydown', onKey as any);
  }, [viewerOpen, viewerItems.length]);

  const openProductGallery = (startIndex: number = 0) => {
    if (!product) return;
    const imgs = (currentImages.length > 0 ? currentImages : (product.images && product.images.length > 0 ? product.images : [product.image]))
      .filter(Boolean)
      .map((u: string) => ({ url: u, type: 'image' as const }));
    if (imgs.length === 0) return;
    setViewerItems(imgs);
    setViewerIndex(Math.min(Math.max(0, startIndex), imgs.length - 1));
    setViewerOpen(true);
  };

  const openReviewMedia = (review: any, startIndex: number = 0) => {
    const items: Array<{ url: string; type: 'image' | 'video' }> = [];
    (review.images || []).forEach((u: string) => items.push({ url: u, type: 'image' }));
    (review.videos || []).forEach((u: string) => items.push({ url: u, type: 'video' }));
    if (items.length === 0) return;
    setViewerItems(items);
    setViewerIndex(Math.min(Math.max(0, startIndex), items.length - 1));
    setViewerOpen(true);
  };

  const handleReviewFileChange = (files: FileList | null) => {
    setNewReview((prev) => ({ ...prev, files: files ? Array.from(files) : [] }));
  };

  const uploadReviewMedia = async (): Promise<{ images: string[]; videos: string[] }> => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
    if (!newReview.files || newReview.files.length === 0) return { images: [], videos: [] };
    const formData = new FormData();
    newReview.files.forEach((f) => formData.append("files", f));
    const res = await fetch(`${API_URL}/api/reviews/upload-media`, {
      method: 'POST',
      headers: userToken ? { 'Authorization': `Bearer ${userToken}` } : undefined,
      body: formData,
    });
    if (!res.ok) throw new Error("upload failed");
    const j = await res.json();
    const dec = j.success && j.encrypted_data ? decryptData(j.encrypted_data) : null;
    return { images: dec?.images || [], videos: dec?.videos || [] };
  };

  // Load addresses for logged-in user to choose from
  useEffect(() => {
    const loadAddresses = async () => {
      if (!isLoggedIn) return;
      try {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
        const res = await fetch(`${API_URL}/api/addresses/`, { headers: { 'Authorization': `Bearer ${userToken}` } });
        if (res.ok) {
          const data = await res.json();
          if (data.success && data.addresses) {
            setAddresses(data.addresses);
            // Default select first address and optimistically enable purchase
            if (data.addresses.length > 0) {
              const firstId = String(data.addresses[0].id);
              setSelectedAddressId(firstId);
              // Optimistically mark serviceable; background verification will correct if needed
              setPincodeStatus({ serviceable: true, message: "" });
            }
          }
        }
      } catch {}
    };
    loadAddresses();
  }, [isLoggedIn, userToken]);

  const checkPincode = async (code: string) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
      const payload = encryptData({ pincode: code.trim() });
      const res = await fetch(`${API_URL}/api/pincode/check`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ payload }) });
      if (!res.ok) throw new Error('fail');
      const j = await res.json();
      const d = j.success && j.encrypted_data ? decryptData(j.encrypted_data) : null;
      const ok = !!d?.serviceable;
      setPincodeStatus({ serviceable: ok, message: ok ? 'Deliverable to this pincode.' : 'We do not deliver to this pincode.' });
    } catch {
      setPincodeStatus({ serviceable: false, message: 'Could not verify pincode.' });
    }
  };

  const checkAddress = async () => {
    if (!selectedAddressId) return;
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
      const payload = encryptData({ address_id: parseInt(selectedAddressId) });
      const res = await fetch(`${API_URL}/api/pincode/check-address`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ payload }) });
      if (!res.ok) throw new Error('fail');
      const j = await res.json();
      const d = j.success && j.encrypted_data ? decryptData(j.encrypted_data) : null;
      const ok = !!d?.serviceable;
      setPincodeStatus({ serviceable: ok, message: ok ? 'Deliverable to selected address.' : 'Selected address is not serviceable.' });
    } catch {
      setPincodeStatus({ serviceable: false, message: 'Could not verify address.' });
    }
  };

  // Auto-verify when user changes the selected address
  useEffect(() => {
    if (selectedAddressId) {
      checkAddress();
    } else if (isLoggedIn) {
      // If cleared, reset status so button disables
      setPincodeStatus(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAddressId]);

  const submitReview = async () => {
    if (!isLoggedIn) { toast.error("Please login to review"); return; }
    if (!product) return;
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
      const media = await uploadReviewMedia();
      const payload = encryptData({
        product_id: product.id,
        rating: newReview.rating,
        title: newReview.title,
        content: newReview.content,
        images: media.images,
        videos: media.videos,
      });
      const res = await fetch(`${API_URL}/api/reviews/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${userToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ payload })
      });
      if (res.ok) {
        toast.success("Review submitted. Awaiting approval.");
        setNewReview({ rating: 5, title: "", content: "", files: [] });
        fetchReviews();
      } else {
        toast.error("Failed to submit review");
      }
    } catch {
      toast.error("Failed to submit review");
    }
  };

  const loadComments = async (reviewId: number) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
      const res = await fetch(`${API_URL}/api/review-comments/review/${reviewId}`);
      if (res.ok) {
        const data = await res.json();
        const dec = data.success && data.encrypted_data ? decryptData(data.encrypted_data) : null;
        const comments = dec?.comments || [];
        setReviews((prev) => prev.map((r) => r.id === reviewId ? { ...r, comments } : r));
      }
    } catch {}
  };

  const submitComment = async (reviewId: number, parentId?: number) => {
    if (!isLoggedIn) { toast.error("Login required"); return; }
    const content = commentDrafts[reviewId] || "";
    if (!content.trim()) return;
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";
      const payload = encryptData({ review_id: reviewId, parent_id: parentId || null, content });
      const res = await fetch(`${API_URL}/api/review-comments/`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${userToken}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ payload })
      });
      if (res.ok) {
        setCommentDrafts((d) => ({ ...d, [reviewId]: "" }));
        await loadComments(reviewId);
      } else {
        toast.error("Failed to comment");
      }
    } catch {
      toast.error("Failed to comment");
    }
  };

  // Check if product is in cart
  const isInCart = product ? cart.some((cartItem) => cartItem.product_id === product.id) : false;
  
  // Check if product is in wishlist
  const isInWishlist = product ? wishlist.some((wishlistItem) => wishlistItem.product_id === product.id) : false;

  // Handle add to cart
  const handleAddToCart = async () => {
    if (!product) return;
    
    if (!isLoggedIn) {
      toast.error("Please login to add to cart");
      return;
    }

    // Validate color and size selection
    if (product.colors && product.colors.length > 0) {
      // New color structure validation
      if (!selectedColorData || !selectedSize) {
        toast.error("Please select a color and size before adding to cart");
        return;
      }
    } else if (product.variants && product.variants.length > 0) {
      // Variant structure validation
      if (!selectedVariant) {
        toast.error("Please select a color and size combination before adding to cart");
        return;
      }
    } else {
      // Fallback to old validation logic
      if (product.sizes && Object.keys(product.sizes).length > 0 && !selectedSize) {
        toast.error("Please select a size before adding to cart");
        return;
      }

      if (product.color && !selectedColor) {
        toast.error("Please select a color before adding to cart");
        return;
      }
    }

    if (isInCart) {
      toast.warning("Product is already in cart!");
      return;
    }

    console.log('🛒 [PRODUCT] Adding to cart:', product.id, 'quantity:', quantity, 'size:', selectedSize, 'color:', selectedColor, 'variant:', selectedVariant?.id);
    const success = await addToCartBackend(product.id, quantity, selectedSize, selectedColor, selectedVariant?.id);
    
    if (success) {
      toast.success("Added to cart successfully!");
    } else {
      toast.error("Failed to add to cart. Please try again.");
    }
  };

  // React to global delivery status changes without refresh
  useEffect(() => {
    const onChange = () => {
      const status = localStorage.getItem('delivery_serviceable') === 'true';
      if (!status) {
        setPincodeStatus({ serviceable: false, message: '' });
      }
    };
    if (typeof window !== 'undefined') {
      window.addEventListener('delivery-change', onChange as any);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('delivery-change', onChange as any);
      }
    };
  }, []);

  // Handle add to wishlist
  const handleAddToWishlist = async () => {
    if (!product) return;
    
    if (!isLoggedIn) {
      toast.error("Please login to add to wishlist");
      return;
    }

    if (isInWishlist) {
      toast.warning("Product is already in wishlist!");
      return;
    }

    console.log('❤️ [PRODUCT] Adding to wishlist:', product.id);
    const success = await addToWishlistBackend(product.id);
    
    if (success) {
      toast.success("Added to wishlist successfully!");
    } else {
      toast.error("Failed to add to wishlist. Please try again.");
    }
  };

  // Handle quantity change
  const handleQuantityChange = (newQuantity: number) => {
    const maxQty = getMaxQuantity();
    if (newQuantity >= 1 && newQuantity <= maxQty) {
      setQuantity(newQuantity);
    }
  };

  const getMaxQuantity = () => {
    if (!product) return 10; // Default max quantity
    
    // Use new color structure if available
    if (selectedColorData && selectedSize) {
      const stock = selectedColorData.sizeCounts[selectedSize] || 0;
      return stock > 0 ? Math.min(stock, 10) : 0;
    }
    
    // Use variant stock if available
    if (selectedVariant) {
      return selectedVariant.stock > 0 ? Math.min(selectedVariant.stock, 10) : 0;
    }
    
    // Fallback to old logic
    if (selectedSize && product.sizes) {
      const sizeStock = product.sizes[selectedSize];
      return sizeStock > 0 ? Math.min(sizeStock, 10) : 0;
    }
    
    return 10; // Default max quantity
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 py-8 mt-20">
          <div className="text-center">
            <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-purple-600 mx-auto"></div>
            <p className="mt-4 text-lg text-gray-600">Loading product...</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 py-8 mt-20">
          <div className="text-center">
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
              <p className="font-bold">Error</p>
              <p>{error || 'Product not found'}</p>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  // Get display price - use variant price if available, otherwise product price
  const displayPrice = selectedVariant 
    ? (selectedVariant.final_price || selectedVariant.price || product.final_price || product.price)
    : (product.final_price || product.price);
  
  const originalPrice = selectedVariant 
    ? (selectedVariant.original_price || product.original_price)
    : product.original_price;
    
  const hasDiscount = originalPrice && originalPrice > displayPrice;

  return (
    <>
      <Navbar />
      <main className="min-h-screen bg-gray-100">
        {/* Hero Section with Background Image */}
        <div className="relative h-96 bg-gradient-to-r from-purple-900 via-blue-900 to-indigo-900 overflow-hidden mt-20">
          <div 
            className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-30"
            style={{
              backgroundImage: `url(${product.images && product.images[0] ? product.images[0] : product.image})`
            }}
          ></div>
          <div className="absolute inset-0 bg-gradient-to-r from-black/50 to-transparent"></div>
          <div className="relative z-10 h-full flex items-center">
            <div className="max-w-7xl mx-auto px-4 w-full">
              <div className="text-white">
                <h1 className="text-4xl md:text-6xl font-bold mb-4 drop-shadow-lg">
                  {product.pname}
                </h1>
                <div className="flex items-center space-x-4 mb-6">
                  <div className="flex items-center space-x-2">
                    <div className="flex">
                      {Array.from({ length: 5 }).map((_, i) => {
                        const displayAvg = reviewStats?.average ?? product.rating ?? 0;
                        const filled = i < Math.round(displayAvg);
                        return <FaStar key={i} className={`w-5 h-5 ${filled ? 'text-yellow-400' : 'text-gray-300'}`} />;
                      })}
                    </div>
                    <span className="text-lg font-medium">
                      {reviewStats?.average ? reviewStats.average.toFixed(1) : (product.rating || 0).toFixed?.(1) || product.rating || 0}
                    </span>
                  </div>
                  <div className="text-2xl font-bold">
                    ₹{displayPrice}
                    {hasDiscount && (
                      <span className="text-lg text-gray-300 line-through ml-2">
                        ₹{originalPrice}
                      </span>
                    )}
                  </div>
                </div>
                {hasDiscount && (
                  <div className="inline-block bg-red-600 text-white px-4 py-2 rounded-full text-sm font-semibold">
                    Save ₹{originalPrice! - displayPrice}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Main Product Content */}
        <div className="max-w-7xl mx-auto px-4 py-8 -mt-16 relative z-20">
          <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 p-8">
          {/* Product Images */}
          <div className="space-y-4">
            {/* Main Image */}
            <div className="aspect-square bg-gradient-to-br from-gray-200 to-gray-300 rounded-xl overflow-hidden cursor-zoom-in shadow-2xl" onClick={() => openProductGallery(selectedImage)}>
              <img
                src={currentImages.length > 0 
                  ? (currentImages[selectedImage] || currentImages[0])
                  : (product.images && product.images[selectedImage] ? product.images[selectedImage] : product.image)
                }
                alt={product.pname}
                className="w-full h-full object-cover"
              />
            </div>
            
            {/* Thumbnail Images */}
            {(currentImages.length > 1 || (product.images && product.images.length > 1)) && (
              <div className="grid grid-cols-4 gap-3">
                {(currentImages.length > 0 ? currentImages : product.images || []).map((image, index) => (
                  <button
                    key={index}
                    onClick={() => setSelectedImage(index)}
                    className={`aspect-square rounded-lg overflow-hidden border-2 transition-all shadow-lg hover:shadow-xl ${
                      selectedImage === index
                        ? 'border-purple-600 ring-2 ring-purple-200 bg-gradient-to-br from-purple-50 to-purple-100'
                        : 'border-gray-300 hover:border-purple-400 bg-gradient-to-br from-gray-100 to-gray-200'
                    }`}
                  >
                    <img
                      src={image}
                      alt={`${product.pname} ${index + 1}`}
                      className="w-full h-full object-cover"
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Product Details */}
          <div className="space-y-6">
            {/* Category */}
            {product.category && (
              <div className="flex items-center space-x-2">
                <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">
                  {product.category}
                </span>
                {product.subcategory && (
                  <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium">
                    {product.subcategory}
                </span>
              )}
            </div>
            )}

            {/* Size Selection */}
            {availableSizes.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                  </div>
                  <label className="block text-lg font-semibold text-gray-800">
                  Select Size
                </label>
                </div>
                <div className="grid grid-cols-4 gap-3">
                  {availableSizes.map((size) => {
                    const isSelected = selectedSize === size;
                    let isAvailable = false;
                    let stock = 0;
                    
                    if (selectedColorData) {
                      // Use new color structure
                      stock = selectedColorData.sizeCounts[size] || 0;
                      isAvailable = stock > 0;
                    } else if (product?.variants) {
                      // Fallback to variant logic
                      isAvailable = product.variants.some(v => v.size === size && v.is_available !== false && v.stock > 0);
                      const variantForSize = product.variants.find(v => v.size === size && v.color === selectedColor);
                      stock = variantForSize?.stock || 0;
                    } else {
                      // Fallback to old logic
                      stock = product?.sizes?.[size] || 0;
                      isAvailable = stock > 0;
                    }
                    
                    return (
                      <button
                        key={size}
                        onClick={() => isAvailable && handleSizeSelection(size)}
                        disabled={!isAvailable}
                        className={`p-4 border-2 rounded-xl text-center font-medium transition-all transform hover:scale-105 ${
                          isSelected
                            ? 'border-purple-600 bg-gradient-to-br from-purple-50 to-purple-100 text-purple-700 shadow-lg ring-2 ring-purple-200'
                            : isAvailable
                            ? 'border-gray-300 hover:border-purple-400 hover:bg-gradient-to-br hover:from-purple-50 hover:to-purple-100 hover:shadow-md text-gray-700'
                            : 'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed'
                        }`}
                      >
                        <div className="text-sm font-bold">{size}</div>
                        <div className="text-xs mt-1">
                          {isAvailable ? (
                            <span className="text-green-600 font-medium">{stock} left</span>
                          ) : (
                            <span className="text-red-500">Out of Stock</span>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
                {!selectedSize && product.available_sizes && product.available_sizes.length > 0 && (
                  <div className="flex items-center space-x-2 text-amber-600 bg-amber-50 p-3 rounded-lg">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                    <span className="text-sm font-medium">Please select a size to continue</span>
                  </div>
                )}
                {selectedSize && (
                  <div className="flex items-center space-x-2 text-green-600 bg-green-50 p-3 rounded-lg">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="text-sm font-medium">
                      Selected: <span className="font-bold">{selectedSize}</span> 
                      <span className="text-gray-600 ml-1">({product.sizes[selectedSize]} available)</span>
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Color Selection */}
            {availableColors.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-pink-100 rounded-full flex items-center justify-center">
                    <svg className="w-5 h-5 text-pink-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zM21 5a2 2 0 00-2-2h-4a2 2 0 00-2 2v12a4 4 0 004 4h4a2 2 0 002-2V5z" />
                    </svg>
                  </div>
                  <label className="block text-lg font-semibold text-gray-800">
                    Select Color
                  </label>
                </div>
                <div className="flex flex-wrap gap-3">
                  {availableColors.map((colorName, index) => {
                    const isSelected = selectedColor === colorName;
                    let isAvailable = true;
                    let colorCode = colorName;
                    
                    if (product?.colors) {
                      // Use new color structure
                      const colorData = product.colors.find(c => c.name === colorName);
                      isAvailable = colorData ? colorData.sizes.some(size => colorData.sizeCounts[size] > 0) : false;
                      colorCode = colorName; // Use color name as color code for now
                    } else if (product?.variants) {
                      // Fallback to variant logic
                      isAvailable = product.variants.some(v => v.color === colorName && v.is_available !== false && v.stock > 0);
                      const variantForColor = product.variants.find(v => v.color === colorName && v.size === selectedSize);
                      colorCode = variantForColor?.color_code || colorName;
                    }
                    
                    return (
                      <div key={index} className="flex items-center space-x-2">
                        <div 
                          className={`w-10 h-10 rounded-full border-2 cursor-pointer transition-all hover:scale-110 ${
                            isSelected
                              ? 'border-purple-600 ring-2 ring-purple-200 shadow-lg'
                              : isAvailable
                              ? 'border-gray-300 hover:border-gray-400 shadow-md'
                              : 'border-gray-200 opacity-50 cursor-not-allowed'
                          }`}
                          style={{ backgroundColor: colorCode }}
                          onClick={() => isAvailable && handleColorSelection(colorName)}
                          title={colorName}
                        />
                        <span className={`text-sm font-medium capitalize ${
                          isAvailable ? 'text-gray-700' : 'text-gray-400'
                        }`}>
                          {colorName}
                        </span>
                      </div>
                    );
                  })}
                </div>
                {selectedColor && (
                  <div className="flex items-center space-x-2 mt-2">
                    <div 
                      className="w-4 h-4 rounded-full border-2 border-purple-600" 
                      style={{ backgroundColor: selectedColorData?.name || selectedColor }}
                    ></div>
                    <p className="text-sm text-green-600">
                      Selected: <span className="font-semibold capitalize">{selectedColor}</span>
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Selected Color/Size Information */}
            {(selectedColorData || selectedVariant) && (
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-4 rounded-xl border-2 border-purple-200">
                <div className="flex items-center space-x-2 mb-2">
                  <div className="w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center">
                    <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-800">Selected Options</h3>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center space-x-3">
                    <div 
                      className="w-8 h-8 rounded-full border-2 border-gray-300 shadow-md"
                      style={{ backgroundColor: selectedColorData?.name || selectedVariant?.color_code || selectedColor }}
                    ></div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Color</p>
                      <p className="text-lg font-semibold text-gray-800 capitalize">
                        {selectedColorData?.name || selectedVariant?.color || selectedColor}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-bold text-gray-700">{selectedSize}</span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Size</p>
                      <p className="text-lg font-semibold text-gray-800">{selectedSize}</p>
                    </div>
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-purple-200">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-600">Stock Available:</span>
                    <span className="text-lg font-bold text-green-600">
                      {selectedColorData && selectedSize 
                        ? selectedColorData.sizeCounts[selectedSize] || 0
                        : selectedVariant?.stock || 0
                      } units
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Rating */}
            <div className="flex items-center gap-2">
              <div className="flex">
                {Array.from({ length: 5 }).map((_, i) => {
                  const displayAvg = reviewStats?.average ?? product.rating ?? 0;
                  const filled = i < Math.round(displayAvg);
                  return <FaStar key={i} className={`w-5 h-5 ${filled ? 'text-yellow-400' : 'text-gray-300'}`} />;
                })}
              </div>
              <span className="text-gray-600 text-sm">
                {reviewStats?.average ? reviewStats.average.toFixed(1) : (product.rating || 0).toFixed?.(1) || product.rating || 0}
                {reviewStats?.total ? ` • ${reviewStats.total} reviews` : ''}
              </span>
            </div>

            {/* Description */}
            {product.pdescription && (
              <div>
                <h3 className="text-lg font-semibold mb-2">Description</h3>
                <p className="text-gray-700 leading-relaxed">{product.pdescription}</p>
              </div>
            )}

            {/* Quantity Selector */}
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                  </svg>
                </div>
                <label className="block text-lg font-semibold text-gray-800">Quantity</label>
              </div>
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => handleQuantityChange(quantity - 1)}
                  disabled={quantity <= 1}
                  className="w-12 h-12 rounded-xl border-2 border-gray-300 flex items-center justify-center hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:scale-105 font-bold text-lg"
                >
                  -
                </button>
                <div className="w-20 h-12 bg-gradient-to-r from-purple-50 to-blue-50 border-2 border-purple-200 rounded-xl flex items-center justify-center">
                  <span className="text-xl font-bold text-purple-700">{quantity}</span>
                </div>
                <button
                  onClick={() => handleQuantityChange(quantity + 1)}
                  disabled={quantity >= getMaxQuantity()}
                  className="w-12 h-12 rounded-xl border-2 border-gray-300 flex items-center justify-center hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all hover:scale-105 font-bold text-lg"
                >
                  +
                </button>
              </div>
              {(selectedColorData || selectedVariant) && (
                <div className="bg-blue-50 p-3 rounded-lg">
                  <p className="text-sm text-blue-700 font-medium">
                    Max quantity: <span className="font-bold">{getMaxQuantity()}</span> 
                    {selectedColorData && selectedSize && (
                      <span> (based on {selectedColorData.name} - {selectedSize} availability)</span>
                    )}
                    {selectedVariant && !selectedColorData && (
                      <span> (based on {selectedVariant.color} - {selectedVariant.size} availability)</span>
                    )}
                  </p>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-4">
              {(() => {
                const canPurchase = isLoggedIn
                  ? (!!selectedAddressId && pincodeStatus?.serviceable === true)
                  : (pincodeStatus?.serviceable === true);
                const disableReason = isLoggedIn
                  ? (!selectedAddressId ? 'Select an address to enable purchase' : (pincodeStatus?.serviceable === false ? 'Address not serviceable' : (!pincodeStatus ? 'Verifying address…' : '')))
                  : (pincodeStatus?.serviceable === false ? 'Pincode not serviceable' : (!pincodeStatus ? 'Enter pincode to check availability' : ''));
                return (
                  <>
                    <button
                      onClick={handleAddToCart}
                      disabled={!canPurchase || isInCart}
                        className={`flex-1 flex items-center justify-center space-x-3 py-4 px-8 rounded-xl font-bold text-lg transition-all transform hover:scale-105 ${
                        isInCart || !canPurchase
                          ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                            : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700 shadow-lg hover:shadow-xl'
                      }`}
                    >
                        <FaShoppingCart className="w-6 h-6" />
                      <span>{isInCart ? 'Already in Cart' : 'Add to Cart'}</span>
                    </button>
              <button
                onClick={handleAddToWishlist}
                disabled={isInWishlist}
                        className={`flex-1 flex items-center justify-center space-x-3 py-4 px-8 rounded-xl font-bold text-lg transition-all transform hover:scale-105 ${
                  isInWishlist
                            ? 'bg-red-100 text-red-700 cursor-not-allowed border-2 border-red-200'
                            : 'bg-white text-purple-600 border-2 border-purple-600 hover:bg-gradient-to-r hover:from-purple-50 hover:to-blue-50 shadow-lg hover:shadow-xl'
                }`}
              >
                        <FaHeart className="w-6 h-6" />
                <span>{isInWishlist ? 'In Wishlist' : 'Add to Wishlist'}</span>
              </button>
                    </>
                  );
                })()}
              </div>
              {(() => {
                const canPurchase = isLoggedIn
                  ? (!!selectedAddressId && pincodeStatus?.serviceable === true)
                  : (pincodeStatus?.serviceable === true);
                const disableReason = isLoggedIn
                  ? (!selectedAddressId ? 'Select an address to enable purchase' : (pincodeStatus?.serviceable === false ? 'Address not serviceable' : (!pincodeStatus ? 'Verifying address…' : '')))
                  : (pincodeStatus?.serviceable === false ? 'Pincode not serviceable' : (!pincodeStatus ? 'Enter pincode to check availability' : ''));
                return !canPurchase && (
                  <div className="bg-amber-50 border-2 border-amber-200 p-4 rounded-xl">
                    <div className="flex items-center space-x-2">
                      <svg className="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                      </svg>
                      <span className="text-sm font-medium text-amber-800">{disableReason}</span>
                    </div>
                  </div>
                );
              })()}
            </div>

            {/* Pincode/Address Check */}
            <div className="mt-6 p-6 border-2 border-gray-200 rounded-xl bg-gradient-to-r from-blue-50 to-purple-50 shadow-lg">
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-800">Check Delivery Availability</h3>
              </div>
              
              {isLoggedIn ? (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Select your address</label>
                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                      <select 
                        className="w-full sm:max-w-md px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white" 
                        value={selectedAddressId} 
                        onChange={(e) => setSelectedAddressId(e.target.value)}
                      >
                        <option value="">Choose your address</option>
                      {addresses.map((a) => (
                          <option key={a.id} value={a.id} className="whitespace-normal break-words">
                            {a.name || 'Address'} - {a.city}, {a.state}
                          </option>
                      ))}
                    </select>
                      <button 
                        onClick={checkAddress} 
                        className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all shadow-md hover:shadow-lg transform hover:-translate-y-0.5 whitespace-nowrap"
                      >
                        Verify
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Enter your pincode</label>
                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                      <input 
                        value={pincode} 
                        onChange={(e) => setPincode(e.target.value)} 
                        className="w-full sm:max-w-md px-4 py-3 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white" 
                        placeholder="e.g., 560001" 
                      />
                      <button 
                        onClick={() => checkPincode(pincode)} 
                        className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all shadow-md hover:shadow-lg transform hover:-translate-y-0.5 whitespace-nowrap"
                      >
                        Check
                      </button>
                    </div>
                  </div>
                </div>
              )}
              
              {pincodeStatus && (
                <div className={`mt-4 p-4 rounded-lg border-2 ${
                  pincodeStatus.serviceable 
                    ? 'bg-green-50 border-green-200' 
                    : 'bg-red-50 border-red-200'
                }`}>
                  <div className="flex items-center space-x-2">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      pincodeStatus.serviceable ? 'bg-green-100' : 'bg-red-100'
                    }`}>
                      {pincodeStatus.serviceable ? (
                        <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      )}
                    </div>
                    <span className={`text-sm font-medium ${
                      pincodeStatus.serviceable ? 'text-green-800' : 'text-red-800'
                    }`}>
                      {pincodeStatus.message}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Product Tags */}
            {product.tag && (
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-gray-700">Tags:</span>
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                  {product.tag}
                </span>
              </div>
            )}

            {/* Product Badges */}
            <div className="flex flex-wrap gap-2">
              {product.is_new && (
                <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                  New
                </span>
              )}
              {product.is_featured && (
                <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                  Featured
                </span>
              )}
              {product.is_latest && (
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
                  Latest
                </span>
              )}
              {product.is_trending && (
                <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm font-medium">
                  Trending
                </span>
              )}
              {product.is_cod_available && (
                <span className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm font-medium">
                  COD Available
                </span>
              )}
            </div>

            {/* Share Buttons */}
            <div className="pt-4 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Share this product</h3>
              <div className="flex space-x-3">
                <button className="p-2 bg-green-500 text-white rounded-full hover:bg-green-600 transition-colors">
                  <FaWhatsapp className="w-5 h-5" />
                </button>
                <button className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors">
                  <FaFacebook className="w-5 h-5" />
                </button>
                <button className="p-2 bg-gray-500 text-white rounded-full hover:bg-gray-600 transition-colors">
                  <FaLink className="w-5 h-5" />
                </button>
              </div>
            </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Similar Products Section */}
      {similarProducts.length > 0 && (
        <section className="bg-gray-50 py-12">
          <div className="max-w-7xl mx-auto px-4">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Similar Products</h2>
              <p className="text-gray-600">You might also like these products</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-6">
              {similarProducts.map((similarProduct) => (
                <div key={similarProduct.id} className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 overflow-hidden group">
                  <div className="aspect-square bg-gradient-to-br from-gray-200 to-gray-300 overflow-hidden">
                    <img
                      src={similarProduct.image}
                      alt={similarProduct.pname}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                    />
                  </div>
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 text-sm mb-2 line-clamp-2 group-hover:text-purple-600 transition-colors">
                      {similarProduct.pname}
                    </h3>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-1">
                        <span className="text-lg font-bold text-purple-600">
                          ₹{similarProduct.final_price || similarProduct.price}
                        </span>
                        {similarProduct.original_price && similarProduct.original_price > (similarProduct.final_price || similarProduct.price) && (
                          <span className="text-sm text-gray-500 line-through">
                            ₹{similarProduct.original_price}
                          </span>
                        )}
                      </div>
                      {similarProduct.rating && (
                        <div className="flex items-center space-x-1">
                          <FaStar className="w-3 h-3 text-yellow-400" />
                          <span className="text-xs text-gray-600">{similarProduct.rating.toFixed(1)}</span>
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => window.location.href = `/product/${similarProduct.id}`}
                      className="w-full mt-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:from-purple-700 hover:to-blue-700 transition-all transform hover:scale-105"
                    >
                      View Product
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Reviews & Comments Two-Column Layout */}
      <section className="bg-white py-12">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Customer Reviews</h2>
              {reviewStats && (
              <div className="flex items-center justify-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className="flex">
                    {Array.from({ length: 5 }).map((_, i) => {
                      const filled = i < Math.round(reviewStats.average);
                      return <FaStar key={i} className={`w-6 h-6 ${filled ? 'text-yellow-400' : 'text-gray-300'}`} />;
                    })}
                  </div>
                  <span className="text-2xl font-bold text-gray-900">{reviewStats.average.toFixed(1)}</span>
                </div>
                <span className="text-gray-600">Based on {reviewStats.total} reviews</span>
              </div>
              )}
            </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left: Reviews List */}
            <div className="lg:col-span-2 space-y-6">
            {reviews.length === 0 && (
                <div className="text-center py-12 bg-gray-50 rounded-2xl">
                  <div className="w-16 h-16 bg-gray-200 rounded-full flex items-center justify-center mx-auto mb-4">
                    <FaStar className="w-8 h-8 text-gray-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">No reviews yet</h3>
                  <p className="text-gray-600">Be the first to review this product!</p>
                </div>
            )}
            {reviews.map((r) => (
                <div key={r.id} className="bg-white border-2 border-gray-100 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-4">
                      <div className="h-12 w-12 rounded-full bg-gradient-to-br from-purple-100 to-blue-100 flex items-center justify-center text-purple-700 text-lg font-bold shadow-md">
                        {(r.author_name || 'U').toString().slice(0,1).toUpperCase()}
                      </div>
                      <div>
                        <div className="flex items-center gap-3 mb-1">
                          <span className="text-lg font-semibold text-gray-900">{r.author_name || 'User'}</span>
                          <div className="flex text-yellow-400">
                            {[...Array(5)].map((_, i) => (<FaStar key={i} className={`w-4 h-4 ${i < (r.rating||0) ? 'text-yellow-400' : 'text-gray-300'}`} />))}
                          </div>
                        </div>
                        <div className="text-sm text-gray-600 font-medium">{r.title || 'Untitled'}</div>
                        <div className="text-xs text-gray-500">{new Date(r.created_at).toLocaleDateString()}</div>
                      </div>
                    </div>
                  </div>
                  <p className="text-gray-800 text-base leading-relaxed mb-4 whitespace-pre-wrap">{r.content}</p>
                {(r.images?.length || r.videos?.length) ? (
                    <div className="flex gap-3 flex-wrap mb-4">
                    {(r.images||[]).map((u: string, idx: number) => (
                        <img key={`ri-${idx}`} src={u} className="w-28 h-28 object-cover rounded-lg cursor-zoom-in shadow-md hover:shadow-lg transition-shadow" alt="review"
                           onClick={() => openReviewMedia(r, idx)} />
                    ))}
                    {(r.videos||[]).map((u: string, idx: number) => (
                        <div key={`rv-${idx}`} className="relative w-36 h-28 rounded-lg overflow-hidden bg-black cursor-pointer shadow-md hover:shadow-lg transition-shadow"
                           onClick={() => openReviewMedia(r, (r.images?.length || 0) + idx)}>
                        <video src={u} className="w-full h-full object-cover opacity-70" />
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                              <svg className="w-4 h-4 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M8 5v14l11-7z"/>
                              </svg>
                            </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : null}
                  <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
                    <button onClick={() => loadComments(r.id)} className="text-sm text-purple-600 hover:text-purple-700 font-medium hover:underline transition-colors">
                      Load comments
                    </button>
                </div>
                  <div className="mt-4 space-y-4">
                  {(r.comments||[]).map((c: any) => (
                      <div key={c.id} className="bg-gray-50 rounded-xl p-4 border border-gray-200">
                        <div className="flex items-center gap-3 mb-2">
                          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center text-blue-700 text-sm font-bold">
                          {(c.author_name || (c.author_type === 'admin' ? 'A' : 'U')).toString().slice(0,1).toUpperCase()}
                        </div>
                          <span className="text-sm font-semibold text-gray-800">{c.author_name || (c.author_type === 'admin' ? 'Admin' : 'User')}</span>
                          {c.author_type === 'admin' && (
                            <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">Admin</span>
                          )}
                      </div>
                        <p className="text-sm text-gray-800 leading-relaxed">{c.content}</p>
                        <div className="pl-4 mt-3 space-y-3">
                        {(c.replies||[]).map((rc: any) => (
                            <div key={rc.id} className="text-sm text-gray-700 flex items-start gap-3">
                              <div className="h-6 w-6 mt-0.5 rounded-full bg-gray-200 flex items-center justify-center text-gray-700 text-xs font-bold">
                              {(rc.author_name || (rc.author_type === 'admin' ? 'A' : 'U')).toString().slice(0,1).toUpperCase()}
                            </div>
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-xs font-semibold text-gray-800">{rc.author_name || (rc.author_type === 'admin' ? 'Admin' : 'User')}</span>
                                  {rc.author_type === 'admin' && (
                                    <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded-full">Admin</span>
                                  )}
                                </div>
                                <div className="text-gray-700">{rc.content}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                  <div className="mt-4 flex gap-2">
                    <input className="flex-1 border rounded px-2 py-1" placeholder="Write a comment" value={commentDrafts[r.id] || ""} onChange={(e) => setCommentDrafts((d) => ({ ...d, [r.id]: e.target.value }))} />
                    <button onClick={() => submitComment(r.id)} className="px-3 py-1 bg-gray-900 text-white rounded">Comment</button>
                  </div>
                </div>
            ))}
            </div>

          {/* Right: Sticky Submit Card */}
          <div className="lg:col-span-1">
            <div className="sticky top-24">
              <div className="p-4 border rounded-lg bg-white shadow-md">
                <h3 className="text-lg font-semibold mb-3">Write a review</h3>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm text-gray-700">Your rating:</span>
                  <div className="flex">
                    {Array.from({ length: 5 }).map((_, i) => {
                      const idx = i + 1;
                      const active = (hoverRating ?? newReview.rating) >= idx;
                      return (
                        <button key={idx} type="button" onMouseEnter={() => setHoverRating(idx)} onMouseLeave={() => setHoverRating(null)} onClick={() => setNewReview((p) => ({ ...p, rating: idx }))} className="p-1" aria-label={`Set rating ${idx}`}>
                          <FaStar className={`w-6 h-6 ${active ? 'text-yellow-400' : 'text-gray-300'}`} />
                        </button>
                      );
                    })}
                  </div>
                  <span className="text-xs text-gray-500">{newReview.rating}/5</span>
                </div>
                <input className="w-full border rounded px-2 py-2 mb-2" placeholder="Title (optional)" value={newReview.title} onChange={(e) => setNewReview((p) => ({ ...p, title: e.target.value }))} />
                <textarea className="w-full border rounded p-2 mb-2" rows={4} placeholder="Share your experience" value={newReview.content} onChange={(e) => setNewReview((p) => ({ ...p, content: e.target.value }))} />
                <input type="file" multiple accept="image/*,video/*" onChange={(e) => handleReviewFileChange(e.target.files)} className="mb-3" />
                <button onClick={submitReview} className="w-full px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700">Submit Review</button>
              </div>
            </div>
          </div>
        </div>
        </div>
      </section>
            
      {/* Media Viewer Modal */}
      {viewerOpen && viewerItems.length > 0 && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center" onClick={() => setViewerOpen(false)}>
          <div className="relative max-w-5xl w-full px-4" onClick={(e) => e.stopPropagation()}>
            <button className="absolute -top-10 right-2 text-white" onClick={() => setViewerOpen(false)}>Close</button>
            <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden flex items-center justify-center">
              {viewerItems[viewerIndex].type === 'image' ? (
                <img src={viewerItems[viewerIndex].url} alt="media" className="max-w-full max-h-full object-contain" />
              ) : (
                <video src={viewerItems[viewerIndex].url} className="w-full h-full" controls autoPlay />
              )}
              {viewerItems.length > 1 && (
                <>
                  <button className="absolute left-2 top-1/2 -translate-y-1/2 bg-white/20 text-white px-3 py-2 rounded" onClick={() => setViewerIndex((i) => (i - 1 + viewerItems.length) % viewerItems.length)}>
                    ‹
                  </button>
                  <button className="absolute right-2 top-1/2 -translate-y-1/2 bg-white/20 text-white px-3 py-2 rounded" onClick={() => setViewerIndex((i) => (i + 1) % viewerItems.length)}>
                    ›
                  </button>
                </>
              )}
            </div>
            {viewerItems.length > 1 && (
              <div className="mt-3 flex gap-2 overflow-x-auto">
                {viewerItems.map((it, i) => (
                  <div key={i} className={`h-14 w-20 rounded overflow-hidden cursor-pointer border ${i === viewerIndex ? 'border-purple-500' : 'border-transparent'}`}
                       onClick={() => setViewerIndex(i)}>
                    {it.type === 'image' ? (
                      <img src={it.url} className="w-full h-full object-cover" />
                    ) : (
                      <video src={it.url} className="w-full h-full object-cover" />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
      <ToastContainer position="bottom-right" />
      <Footer />
    </>
  );
}