import React, { useState, useEffect } from "react";
import {
    Box,
    Card,
    CardContent,
    CardMedia,
    Typography,
    Grid,
    Chip,
    Stack,
    Button,
    Alert,
    CircularProgress,
    ImageList,
    ImageListItem,
    Badge,
} from "@mui/material";
import axios from "axios";
import { decryptPayload } from "../utils/crypto";
import ProductDetail from "./product_detail";

const CustomerProductList = () => {
    const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
    
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [selectedProductId, setSelectedProductId] = useState(null);

    useEffect(() => {
        fetchProducts();
    }, []);

    const fetchProducts = async () => {
        try {
            setLoading(true);
            const res = await axios.get(`${API_URL}/api/products/customer`);
            if (res.data.success && res.data.encrypted_data) {
                const decrypted = decryptPayload(res.data.encrypted_data);
                setProducts(decrypted.products || []);
            }
        } catch (err) {
            setError("Failed to fetch products");
        } finally {
            setLoading(false);
        }
    };

    const normalizeImageUrl = (url) => {
        if (!url) return url;
        if (url.startsWith('http://') || url.startsWith('https://')) return url;
        const base = API_URL.replace(/\/$/, '');
        const path = url.startsWith('/') ? url : `/${url}`;
        return `${base}${path}`;
    };

    const renderProductImages = (product) => {
        // Show main product images first
        const mainImages = product.images || [];
        const colorImages = product.colors?.flatMap(color => color.images || []) || [];
        const allImages = [...mainImages, ...colorImages];

        if (allImages.length === 0) {
            return (
                <Box sx={{ height: 200, bgcolor: 'grey.100', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Typography variant="body2" color="text.secondary">No images</Typography>
                </Box>
            );
        }

        return (
            <ImageList cols={1} gap={0} sx={{ height: 200 }}>
                {allImages.slice(0, 3).map((url, idx) => (
                    <ImageListItem key={idx}>
                        <img 
                            src={normalizeImageUrl(url)} 
                            alt={`Product ${idx + 1}`}
                            loading="lazy"
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                    </ImageListItem>
                ))}
            </ImageList>
        );
    };

    const renderColorSizes = (product) => {
        if (!product.colors || product.colors.length === 0) {
            // Legacy single color/size display
            if (product.color && product.sizes) {
                return (
                    <Box>
                        <Chip label={product.color} size="small" sx={{ mb: 1 }} />
                        <Stack direction="row" spacing={0.5} flexWrap="wrap">
                            {Object.entries(product.sizes).map(([size, count]) => (
                                <Chip 
                                    key={size} 
                                    label={`${size}: ${count}`} 
                                    size="small" 
                                    variant="outlined"
                                    color={count > 0 ? "primary" : "default"}
                                />
                            ))}
                        </Stack>
                    </Box>
                );
            }
            return <Typography variant="body2" color="text.secondary">No size info</Typography>;
        }

        // New color-based display
        return (
            <Box>
                {product.colors.map((color, idx) => (
                    <Box key={idx} sx={{ mb: 1 }}>
                        <Chip 
                            label={color.name} 
                            size="small" 
                            sx={{ 
                                mb: 0.5,
                                bgcolor: color.name ? `${color.name}22` : undefined
                            }} 
                        />
                        <Stack direction="row" spacing={0.5} flexWrap="wrap">
                            {Object.entries(color.sizeCounts || {}).map(([size, count]) => (
                                <Chip 
                                    key={size} 
                                    label={`${size}: ${count}`} 
                                    size="small" 
                                    variant="outlined"
                                    color={count > 0 ? "primary" : "default"}
                                />
                            ))}
                        </Stack>
                    </Box>
                ))}
            </Box>
        );
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" p={4}>
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Alert severity="error" sx={{ m: 2 }}>
                {error}
            </Alert>
        );
    }

    return (
        <Box sx={{ p: 2 }}>
            <Typography variant="h4" gutterBottom>
                Our Products
            </Typography>
            
            <Grid container spacing={3}>
                {products.map((product) => (
                    <Grid item xs={12} sm={6} md={4} lg={3} key={product.id}>
                        <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                            {renderProductImages(product)}
                            
                            <CardContent sx={{ flexGrow: 1 }}>
                                <Typography variant="h6" gutterBottom noWrap>
                                    {product.pname}
                                </Typography>
                                
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                    {product.pdescription?.substring(0, 100)}...
                                </Typography>

                                {/* Colors and Sizes */}
                                <Box sx={{ mb: 2 }}>
                                    <Typography variant="subtitle2" gutterBottom>
                                        Available Colors & Sizes:
                                    </Typography>
                                    {renderColorSizes(product)}
                                </Box>

                                {/* Pricing */}
                                <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
                                    <Typography variant="h6" color="primary">
                                        ₹{product.final_price || product.price}
                                    </Typography>
                                    {product.discount_value > 0 && (
                                        <>
                                            <Typography variant="body2" color="text.secondary" sx={{ textDecoration: 'line-through' }}>
                                                ₹{product.original_price || product.price}
                                            </Typography>
                                            <Chip 
                                                label={`${product.discount_value}% OFF`} 
                                                size="small" 
                                                color="error" 
                                            />
                                        </>
                                    )}
                                </Stack>

                                {/* Stock Status */}
                                <Box sx={{ mb: 2 }}>
                                    <Chip 
                                        label={`Stock: ${product.stock || 0}`} 
                                        size="small" 
                                        color={product.stock > 0 ? "success" : "error"}
                                    />
                                </Box>

                                {/* Product Features */}
                                <Stack direction="row" spacing={1} flexWrap="wrap">
                                    {product.is_featured && <Chip label="Featured" size="small" color="primary" />}
                                    {product.is_latest && <Chip label="Latest" size="small" color="secondary" />}
                                    {product.is_trending && <Chip label="Trending" size="small" color="warning" />}
                                    {product.is_new && <Chip label="New" size="small" color="success" />}
                                </Stack>

                                {/* Action Buttons */}
                                <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
                                    <Button variant="contained" size="small" fullWidth>
                                        Add to Cart
                                    </Button>
                                    <Button variant="outlined" size="small">
                                        View Details
                                    </Button>
                                </Stack>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>

            {products.length === 0 && (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography variant="h6" color="text.secondary">
                        No products available at the moment
                    </Typography>
                </Box>
            )}
        </Box>
    );
};

export default CustomerProductList;
