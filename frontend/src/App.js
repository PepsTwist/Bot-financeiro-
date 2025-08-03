import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  PieChart, 
  BarChart3, 
  Wallet,
  Bot,
  MessageSquare,
  ArrowUpRight,
  ArrowDownRight,
  Calendar,
  RefreshCw
} from 'lucide-react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [telegramId, setTelegramId] = useState('');
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchDashboard = async (id) => {
    if (!id) return;
    
    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/dashboard/${id}`);
      setDashboardData(response.data);
    } catch (err) {
      setError('Erro ao carregar dados. Verifique o ID do Telegram.');
      console.error('Error fetching dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchDashboard(telegramId);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const CategoryChart = ({ categories }) => {
    const expenseCategories = Object.entries(categories)
      .filter(([_, data]) => data.expense > 0)
      .sort(([, a], [, b]) => b.expense - a.expense);

    const total = expenseCategories.reduce((sum, [_, data]) => sum + data.expense, 0);

    const colors = [
      '#1f2937', '#374151', '#6b7280', '#9ca3af', '#d1d5db',
      '#f59e0b', '#d97706', '#b45309', '#92400e', '#78350f'
    ];

    return (
      <div className="space-y-4">
        {expenseCategories.map(([category, data], index) => {
          const percentage = ((data.expense / total) * 100).toFixed(1);
          
          return (
            <div key={category} className="flex items-center justify-between">
              <div className="flex items-center space-x-3 flex-1">
                <div 
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: colors[index % colors.length] }}
                />
                <span className="text-sm font-medium text-gray-700">{category}</span>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="text-sm font-semibold text-gray-900">
                    {formatCurrency(data.expense)}
                  </div>
                  <div className="text-xs text-gray-500">{percentage}%</div>
                </div>
                <div className="w-16 bg-gray-200 rounded-full h-2">
                  <div 
                    className="h-2 rounded-full"
                    style={{ 
                      width: `${percentage}%`,
                      backgroundColor: colors[index % colors.length]
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-slate-800 to-slate-600 p-2 rounded-xl">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">FinanceBot</h1>
                <p className="text-sm text-slate-600">Gestão Financeira Inteligente</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                Telegram Bot Ativo
              </Badge>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="space-y-4">
                <Badge className="bg-slate-700 text-slate-200 hover:bg-slate-600">
                  🤖 Bot do Telegram + IA
                </Badge>
                <h1 className="text-4xl lg:text-6xl font-bold leading-tight">
                  Controle suas 
                  <span className="bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent"> Finanças </span>
                  pelo Telegram
                </h1>
                <p className="text-xl text-slate-300 leading-relaxed">
                  Digite suas transações em linguagem natural e nossa IA categoriza automaticamente. 
                  Visualize seus gastos em tempo real.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-4">
                <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                  <div className="flex items-center space-x-3 mb-2">
                    <MessageSquare className="w-5 h-5 text-blue-400" />
                    <span className="font-semibold">Exemplo de uso:</span>
                  </div>
                  <div className="space-y-2 text-sm text-slate-300">
                    <div>"Paguei R$ 500 de aluguel"</div>
                    <div>"Recebi R$ 2000 de salário"</div>
                    <div>"Gastei 50 no supermercado"</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="relative">
              <div className="bg-gradient-to-r from-slate-800 to-slate-700 rounded-2xl p-1">
                <img 
                  src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwxfHxmaW5hbmNpYWwlMjBkYXNoYm9hcmR8ZW58MHx8fHwxNzU0MTIxMjg0fDA&ixlib=rb-4.1.0&q=85"
                  alt="Financial Dashboard"
                  className="w-full h-[400px] object-cover rounded-xl shadow-2xl"
                />
              </div>
              
              <div className="absolute -top-6 -right-6 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-full p-4">
                <BarChart3 className="w-8 h-8 text-white" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Access Dashboard */}
      <section className="py-12 bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">
              Acesse seu Dashboard
            </h2>
            <p className="text-lg text-slate-600">
              Digite seu ID do Telegram para visualizar suas transações e gráficos
            </p>
          </div>

          <Card className="max-w-md mx-auto">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bot className="w-5 h-5" />
                ID do Telegram
              </CardTitle>
              <CardDescription>
                Para encontrar seu ID, envie /start para o bot no Telegram
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                  type="number"
                  placeholder="Ex: 123456789"
                  value={telegramId}
                  onChange={(e) => setTelegramId(e.target.value)}
                  disabled={loading}
                />
                <Button 
                  type="submit" 
                  className="w-full bg-slate-900 hover:bg-slate-800"
                  disabled={loading || !telegramId}
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Carregando...
                    </>
                  ) : (
                    <>
                      <BarChart3 className="w-4 h-4 mr-2" />
                      Ver Dashboard
                    </>
                  )}
                </Button>
              </form>
              
              {error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {error}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Dashboard */}
      {dashboardData && (
        <section className="py-12 bg-slate-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {dashboardData.user ? (
              <>
                {/* User Info */}
                <div className="mb-8 text-center">
                  <h2 className="text-3xl font-bold text-slate-900 mb-2">
                    Dashboard de {dashboardData.user.name || 'Usuário'}
                  </h2>
                  <Badge variant="outline" className="text-slate-600">
                    ID: {telegramId}
                  </Badge>
                </div>

                {/* Balance Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Saldo Atual</CardTitle>
                      <Wallet className="h-4 w-4 text-slate-600" />
                    </CardHeader>
                    <CardContent>
                      <div className={`text-2xl font-bold ${dashboardData.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(dashboardData.balance)}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Receitas (30d)</CardTitle>
                      <ArrowUpRight className="h-4 w-4 text-green-600" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-green-600">
                        {formatCurrency(dashboardData.monthly_summary.income)}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Despesas (30d)</CardTitle>
                      <ArrowDownRight className="h-4 w-4 text-red-600" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold text-red-600">
                        {formatCurrency(dashboardData.monthly_summary.expense)}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Resultado (30d)</CardTitle>
                      <TrendingUp className="h-4 w-4 text-slate-600" />
                    </CardHeader>
                    <CardContent>
                      <div className={`text-2xl font-bold ${dashboardData.monthly_summary.net >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(dashboardData.monthly_summary.net)}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Charts and Transactions */}
                <Tabs defaultValue="categories" className="space-y-4">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="categories" className="flex items-center gap-2">
                      <PieChart className="w-4 h-4" />
                      Categorias
                    </TabsTrigger>
                    <TabsTrigger value="transactions" className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      Transações
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="categories" className="space-y-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <PieChart className="w-5 h-5" />
                          Gastos por Categoria
                        </CardTitle>
                        <CardDescription>
                          Distribuição das suas despesas por categoria
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        {Object.keys(dashboardData.categories).length > 0 ? (
                          <CategoryChart categories={dashboardData.categories} />
                        ) : (
                          <div className="text-center py-8 text-slate-500">
                            Nenhuma transação encontrada. Comece enviando mensagens para o bot!
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </TabsContent>

                  <TabsContent value="transactions" className="space-y-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <Calendar className="w-5 h-5" />
                          Transações Recentes
                        </CardTitle>
                        <CardDescription>
                          Suas últimas 50 transações
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        {dashboardData.transactions && dashboardData.transactions.length > 0 ? (
                          <div className="space-y-3 max-h-96 overflow-y-auto">
                            {dashboardData.transactions.map((transaction, index) => (
                              <div key={transaction.id || index} className="flex items-center justify-between p-4 border border-slate-200 rounded-lg bg-white hover:bg-slate-50 transition-colors">
                                <div className="flex items-center space-x-3">
                                  <div className={`p-2 rounded-full ${transaction.type === 'income' ? 'bg-green-100' : 'bg-red-100'}`}>
                                    {transaction.type === 'income' ? (
                                      <ArrowUpRight className={`w-4 h-4 text-green-600`} />
                                    ) : (
                                      <ArrowDownRight className={`w-4 h-4 text-red-600`} />
                                    )}
                                  </div>
                                  <div>
                                    <div className="font-medium text-slate-900">
                                      {transaction.description}
                                    </div>
                                    <div className="text-sm text-slate-500">
                                      {transaction.category} • {formatDate(transaction.date)}
                                    </div>
                                  </div>
                                </div>
                                <div className={`font-semibold ${transaction.type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                                  {transaction.type === 'income' ? '+' : '-'}{formatCurrency(transaction.amount)}
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-center py-8 text-slate-500">
                            Nenhuma transação encontrada. Envie suas primeiras transações para o bot!
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </TabsContent>
                </Tabs>
              </>
            ) : (
              <div className="text-center py-12">
                <Bot className="w-16 h-16 text-slate-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-slate-900 mb-2">
                  Usuário não encontrado
                </h3>
                <p className="text-slate-600">
                  Envie uma mensagem para o bot no Telegram primeiro, depois tente novamente.
                </p>
              </div>
            )}
          </div>
        </section>
      )}

      {/* How it Works */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-slate-900 mb-4">
              Como Funciona
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Sistema simples e inteligente para controlar suas finanças através do Telegram
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-gradient-to-r from-blue-500 to-blue-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <MessageSquare className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">
                1. Envie uma Mensagem
              </h3>
              <p className="text-slate-600">
                Digite suas transações em linguagem natural no bot do Telegram
              </p>
            </div>

            <div className="text-center">
              <div className="bg-gradient-to-r from-emerald-500 to-emerald-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Bot className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">
                2. IA Processa
              </h3>
              <p className="text-slate-600">
                Nossa IA extrai valor, categoria e descrição automaticamente
              </p>
            </div>

            <div className="text-center">
              <div className="bg-gradient-to-r from-purple-500 to-purple-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-2">
                3. Visualize Gráficos
              </h3>
              <p className="text-slate-600">
                Acesse este painel para ver seus gastos organizados em gráficos
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <div className="bg-gradient-to-r from-slate-700 to-slate-600 p-2 rounded-xl">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-bold">FinanceBot</h3>
            </div>
            <p className="text-slate-400 mb-6">
              Controle suas finanças de forma inteligente com IA e Telegram
            </p>
            
            <div className="bg-slate-800 rounded-xl p-6 max-w-md mx-auto">
              <h4 className="font-semibold mb-3">🤖 Como começar:</h4>
              <div className="text-sm text-slate-300 space-y-1">
                <div>1. Encontre nosso bot no Telegram</div>
                <div>2. Envie /start para começar</div>
                <div>3. Digite suas transações naturalmente</div>
                <div>4. Acesse este painel com seu ID</div>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;