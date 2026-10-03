"use client";

import React, { useEffect, useState } from "react";
import { ShoppingCart, Plus, Trash2, Search, Receipt, CheckCircle2, ChevronRight, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  listProducts,
  listCustomers,
  createProductSale,
  listProductSales,
  ApiError,
  Product,
  Customer,
  ProductSale
} from "@/lib/api";
import { getActiveBusinessId } from "@/lib/business";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY" }).format(amount);
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString("tr-TR");
}

interface CartItem {
  product: Product;
  quantity: number;
  unit_price: number;
  total: number;
}

export default function ProductSalesPage() {
  const businessId = getActiveBusinessId();

  const [products, setProducts] = useState<Product[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [sales, setSales] = useState<ProductSale[]>([]);
  
  const [search, setSearch] = useState("");
  const [filteredProducts, setFilteredProducts] = useState<Product[]>([]);
  
  const [cart, setCart] = useState<CartItem[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>("");
  const [paymentMethod, setPaymentMethod] = useState("CREDIT_CARD");
  const [notes, setNotes] = useState("");
  
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [expandedSale, setExpandedSale] = useState<string | null>(null);

  const refreshData = async () => {
    if (!businessId) return;
    setLoading(true);
    try {
      const [prodRes, custRes, salesRes] = await Promise.all([
        listProducts(businessId, { status: "ACTIVE", size: 100 }),
        listCustomers(businessId, 1, 100),
        listProductSales(businessId, { page: 1 })
      ]);
      setProducts(prodRes);
      setFilteredProducts(prodRes);
      setCustomers(custRes);
      setSales(salesRes);
    } catch (err) {
      toast.error("Veriler yüklenirken hata oluştu.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (businessId) refreshData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [businessId]);

  useEffect(() => {
    if (search.trim() === "") {
      setFilteredProducts(products);
    } else {
      const lower = search.toLowerCase();
      setFilteredProducts(products.filter(p => p.name.toLowerCase().includes(lower) || (p.sku && p.sku.toLowerCase().includes(lower))));
    }
  }, [search, products]);

  const addToCart = (product: Product) => {
    if (product.current_stock <= 0) {
      toast.error("Bu ürün stokta yok!");
      return;
    }
    
    setCart(prev => {
      const existing = prev.find(item => item.product.id === product.id);
      if (existing) {
        if (existing.quantity >= product.current_stock) {
          toast.error("Yetersiz stok!");
          return prev;
        }
        return prev.map(item => 
          item.product.id === product.id 
            ? { ...item, quantity: item.quantity + 1, total: (item.quantity + 1) * item.unit_price } 
            : item
        );
      } else {
        return [...prev, { product, quantity: 1, unit_price: product.sale_price, total: product.sale_price }];
      }
    });
  };

  const updateCartQuantity = (productId: string, qty: number) => {
    if (qty <= 0) {
      removeFromCart(productId);
      return;
    }
    const product = products.find(p => p.id === productId);
    if (product && qty > product.current_stock) {
      toast.error("Yetersiz stok!");
      return;
    }

    setCart(prev => prev.map(item => 
      item.product.id === productId 
        ? { ...item, quantity: qty, total: qty * item.unit_price } 
        : item
    ));
  };

  const removeFromCart = (productId: string) => {
    setCart(prev => prev.filter(item => item.product.id !== productId));
  };

  const cartSubtotal = cart.reduce((sum, item) => sum + item.total, 0);

  const handleCompleteSale = async () => {
    if (!businessId) return;
    if (cart.length === 0) {
      toast.error("Sepet boş.");
      return;
    }

    setCompleting(true);
    try {
      const payload = {
        customer_id: selectedCustomerId || null,
        payment_method: paymentMethod,
        notes: notes || null,
        items: cart.map(item => ({
          product_id: item.product.id,
          quantity: item.quantity,
          unit_price: item.unit_price
        }))
      };

      await createProductSale(businessId, payload);
      toast.success("Satış tamamlandı.");
      
      // Reset form
      setCart([]);
      setSelectedCustomerId("");
      setNotes("");
      setSearch("");
      
      refreshData();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Satış tamamlanamadı.");
    } finally {
      setCompleting(false);
    }
  };

  const toggleSaleRow = (saleId: string) => {
    setExpandedSale(expandedSale === saleId ? null : saleId);
  };

  if (!businessId) return <div className="p-6">Yükleniyor...</div>;

  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Ürün Satışı</h1>
        <p className="mt-1 text-sm text-ink-muted">Hızlı satış yapın ve satış geçmişini görüntüleyin.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Product Search & List */}
        <div className="lg:col-span-2 space-y-4">
          <Card className="bg-surface-elevated border-border h-[calc(100vh-220px)] flex flex-col">
            <CardHeader className="pb-3 border-b border-border">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-muted" />
                <Input 
                  placeholder="Ürün adı veya barkod okutun..." 
                  className="pl-9 bg-surface text-lg py-6"
                  value={search}
                  onChange={e => setSearch(e.target.value)}
                  autoFocus
                />
              </div>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-4">
              {loading ? <div className="text-center text-ink-muted mt-10">Yükleniyor...</div> : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {filteredProducts.map(prod => (
                    <div 
                      key={prod.id} 
                      onClick={() => addToCart(prod)}
                      className={cn(
                        "p-3 rounded-lg border border-border bg-surface hover:border-accent cursor-pointer transition-colors flex flex-col justify-between h-24",
                        prod.current_stock <= 0 && "opacity-50 cursor-not-allowed hover:border-border"
                      )}
                    >
                      <div className="font-medium text-sm line-clamp-2 leading-tight">{prod.name}</div>
                      <div className="flex justify-between items-end mt-2">
                        <span className="font-bold text-accent">{formatCurrency(prod.sale_price)}</span>
                        <span className={cn("text-xs font-medium", prod.current_stock > 0 ? "text-emerald-500" : "text-red-500")}>
                          {prod.current_stock} {prod.unit}
                        </span>
                      </div>
                    </div>
                  ))}
                  {filteredProducts.length === 0 && <div className="col-span-full text-center text-ink-muted py-8">Ürün bulunamadı.</div>}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Cart & Checkout */}
        <div className="space-y-4">
          <Card className="bg-surface-elevated border-border border-t-4" style={{ borderTopColor: "var(--agent-sales)" }}>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2"><ShoppingCart className="h-5 w-5" /> Sepet</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {cart.length === 0 ? (
                  <div className="text-center py-8 text-ink-muted bg-surface rounded-md border border-dashed border-border">
                    Sepetiniz boş.<br/>Sol taraftan ürün ekleyin.
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
                    {cart.map(item => (
                      <div key={item.product.id} className="flex flex-col gap-2 p-2 bg-surface rounded-md border border-border">
                        <div className="flex justify-between items-start">
                          <span className="font-medium text-sm">{item.product.name}</span>
                          <Button variant="ghost" size="icon" className="h-5 w-5 text-danger" onClick={() => removeFromCart(item.product.id)}><Trash2 className="h-3 w-3" /></Button>
                        </div>
                        <div className="flex justify-between items-center">
                          <div className="flex items-center gap-1">
                            <Button variant="outline" size="icon" className="h-6 w-6" onClick={() => updateCartQuantity(item.product.id, item.quantity - 1)}>-</Button>
                            <Input type="number" className="h-6 w-12 text-center text-xs px-1" value={item.quantity} onChange={e => updateCartQuantity(item.product.id, parseInt(e.target.value) || 0)} />
                            <Button variant="outline" size="icon" className="h-6 w-6" onClick={() => updateCartQuantity(item.product.id, item.quantity + 1)}>+</Button>
                          </div>
                          <span className="font-bold text-sm">{formatCurrency(item.total)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                <div className="pt-4 border-t border-border space-y-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Müşteri (Opsiyonel)</Label>
                    <select className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:outline-none" value={selectedCustomerId} onChange={e => setSelectedCustomerId(e.target.value)}>
                      <option value="">Genel Müşteri</option>
                      {customers.map(c => <option key={c.id} value={c.id}>{c.first_name} {c.last_name}</option>)}
                    </select>
                  </div>
                  
                  <div className="space-y-1">
                    <Label className="text-xs">Ödeme Yöntemi</Label>
                    <div className="flex gap-2">
                      <Button variant={paymentMethod === 'CASH' ? 'default' : 'outline'} className={cn("flex-1 h-8 text-xs", paymentMethod === 'CASH' && "bg-emerald-600")} onClick={() => setPaymentMethod('CASH')}>Nakit</Button>
                      <Button variant={paymentMethod === 'CREDIT_CARD' ? 'default' : 'outline'} className={cn("flex-1 h-8 text-xs", paymentMethod === 'CREDIT_CARD' && "bg-blue-600")} onClick={() => setPaymentMethod('CREDIT_CARD')}>Kredi K.</Button>
                    </div>
                  </div>

                  <div className="space-y-1">
                    <Label className="text-xs">Notlar</Label>
                    <Input className="h-8 text-xs" value={notes} onChange={e => setNotes(e.target.value)} placeholder="Satış notu..." />
                  </div>

                  <div className="bg-surface p-3 rounded-lg border border-border mt-2">
                    <div className="flex justify-between text-sm text-ink-muted mb-1"><span>Ara Toplam</span><span>{formatCurrency(cartSubtotal)}</span></div>
                    <div className="flex justify-between font-bold text-lg mt-2 pt-2 border-t border-border"><span>Genel Toplam</span><span className="text-accent">{formatCurrency(cartSubtotal)}</span></div>
                  </div>

                  <Button 
                    className="w-full h-12 text-md gap-2" 
                    style={{ backgroundColor: "var(--agent-sales)" }}
                    disabled={cart.length === 0 || completing}
                    onClick={handleCompleteSale}
                  >
                    <CheckCircle2 className="h-5 w-5" />
                    {completing ? "Tamamlanıyor..." : "Satışı Tamamla"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Recent Sales Table */}
      <Card className="bg-surface-elevated border-border">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2"><Receipt className="h-5 w-5 text-ink-muted" /> Son Satışlar</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && sales.length === 0 ? <div className="text-center py-4 text-ink-muted">Yükleniyor...</div> : sales.length === 0 ? <div className="text-center py-4 text-ink-muted">Henüz satış yapılmadı.</div> : (
            <div className="overflow-hidden">
              <table className="w-full text-sm text-left">
                <thead className="bg-surface text-ink-muted text-xs uppercase">
                  <tr>
                    <th className="px-4 py-3 w-8"></th>
                    <th className="px-4 py-3">Tarih</th>
                    <th className="px-4 py-3">Müşteri</th>
                    <th className="px-4 py-3">Ödeme</th>
                    <th className="px-4 py-3 text-right">Tutar</th>
                  </tr>
                </thead>
                <tbody>
                  {sales.map(sale => (
                    <React.Fragment key={sale.id}>
                      <tr className="border-t border-border hover:bg-white/[0.02]">
                        <td className="px-4 py-3">
                          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => toggleSaleRow(sale.id)}>
                            {expandedSale === sale.id ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                          </Button>
                        </td>
                        <td className="px-4 py-3">{formatDate(sale.sale_date)}</td>
                        <td className="px-4 py-3">{sale.customer_id ? "Kayıtlı Müşteri" : "Genel Müşteri"}</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-1 bg-surface rounded text-xs">{sale.payment_method === 'CASH' ? 'Nakit' : sale.payment_method === 'CREDIT_CARD' ? 'Kredi Kartı' : sale.payment_method}</span>
                        </td>
                        <td className="px-4 py-3 text-right font-bold text-emerald-500">{formatCurrency(sale.total_amount)}</td>
                      </tr>
                      {expandedSale === sale.id && (
                        <tr className="border-b border-border bg-black/10">
                          <td colSpan={5} className="px-8 py-3">
                            <table className="w-full text-xs">
                              <thead className="text-ink-muted border-b border-white/5">
                                <tr><th className="text-left pb-1">Ürün</th><th className="text-center pb-1">Miktar</th><th className="text-right pb-1">Birim Fiyat</th><th className="text-right pb-1">Toplam</th></tr>
                              </thead>
                              <tbody>
                                {sale.items.map((item, idx) => (
                                  <tr key={idx} className="border-b border-white/5 last:border-0">
                                    <td className="py-2">{item.product_name}</td>
                                    <td className="py-2 text-center">{item.quantity}</td>
                                    <td className="py-2 text-right">{formatCurrency(item.unit_price)}</td>
                                    <td className="py-2 text-right font-medium">{formatCurrency(item.total)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                            {sale.notes && <div className="mt-2 text-xs text-ink-muted">Not: {sale.notes}</div>}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
