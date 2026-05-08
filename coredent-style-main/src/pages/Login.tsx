// ============================================
// CoreDent PMS - Login Page
// UI for authentication (logic handled by external API)
// ============================================

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/auth-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Stethoscope, Eye, EyeOff, Loader2, AlertTriangle } from 'lucide-react';
import { z } from 'zod';
import { Alert, AlertDescription } from '@/components/ui/alert';

const loginSchema = z.object({
  email: z.string().trim().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const [backupCode, setBackupCode] = useState('');
  const [useBackupCode, setUseBackupCode] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<{ email?: string; password?: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loginError, setLoginError] = useState<string | null>(null);
  
  const { login, verifyMfa, pendingMfaChallenge, clearMfaChallenge } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    setLoginError(null);

    // Validate input
    const result = loginSchema.safeParse({ email, password });
    
    if (!result.success) {
      const fieldErrors: { email?: string; password?: string } = {};
      result.error.issues.forEach((issue) => {
        const field = issue.path[0] as 'email' | 'password';
        fieldErrors[field] = issue.message;
      });
      setErrors(fieldErrors);
      return;
    }

    setIsSubmitting(true);
    
    const result = await login({ email, password });
    
    if (result.success) {
      navigate('/dashboard');
    } else if (result.mfaRequired) {
      setLoginError(null);
    } else {
      setLoginError(result.message || 'Invalid email or password. Please try again.');
    }
    
    setIsSubmitting(false);
  };

  const handleMfaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);

    if (!useBackupCode && !/^\d{6}$/.test(mfaCode)) {
      setLoginError('Enter a valid 6-digit authenticator code.');
      return;
    }

    if (useBackupCode && backupCode.trim().length < 8) {
      setLoginError('Enter a valid backup code.');
      return;
    }

    setIsSubmitting(true);
    const success = await verifyMfa(mfaCode, useBackupCode ? backupCode.toUpperCase() : undefined);
    if (success) {
      navigate('/dashboard');
    }
    setIsSubmitting(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30 p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary mb-4">
            <Stethoscope className="h-8 w-8 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-bold">CoreDent</h1>
          <p className="text-muted-foreground">Dental Practice Management</p>
        </div>

        {/* Login Card */}
        <Card className="shadow-lg">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center">
              {pendingMfaChallenge ? 'Two-Factor Authentication' : 'Welcome back'}
            </CardTitle>
            <CardDescription className="text-center">
              {pendingMfaChallenge
                ? `Enter your verification code for ${pendingMfaChallenge.email}`
                : 'Sign in to your account to continue'}
            </CardDescription>
          </CardHeader>
          
          <form onSubmit={pendingMfaChallenge ? handleMfaSubmit : handleSubmit}>
            <CardContent className="space-y-4">
              {/* M-3 FIX: Inline login error message */}
              {loginError && (
                <Alert variant="destructive" className="animate-in fade-in slide-in-from-top-2 duration-300">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>{loginError}</AlertDescription>
                </Alert>
              )}
              {pendingMfaChallenge ? (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="mfaCode">Authenticator Code</Label>
                    <Input
                      id="mfaCode"
                      type="text"
                      inputMode="numeric"
                      placeholder="123456"
                      value={mfaCode}
                      onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      disabled={isSubmitting || useBackupCode}
                      autoComplete="one-time-code"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="backupCode">Backup Code (optional)</Label>
                    <Input
                      id="backupCode"
                      type="text"
                      placeholder="A1B2C3D4"
                      value={backupCode}
                      onChange={(e) => setBackupCode(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 8))}
                      disabled={isSubmitting || !useBackupCode}
                    />
                  </div>
                  <Button
                    type="button"
                    variant="link"
                    className="h-auto px-0 text-sm"
                    onClick={() => setUseBackupCode((prev) => !prev)}
                  >
                    {useBackupCode ? 'Use authenticator code instead' : 'Use backup code instead'}
                  </Button>
                </>
              ) : (
                <>
                  {/* Email Field */}
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="you@practice.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className={errors.email ? 'border-destructive' : ''}
                      disabled={isSubmitting}
                      autoComplete="email"
                    />
                    {errors.email && (
                      <p className="text-sm text-destructive">{errors.email}</p>
                    )}
                  </div>

                  {/* Password Field */}
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className={errors.password ? 'border-destructive pr-10' : 'pr-10'}
                        disabled={isSubmitting}
                        autoComplete="current-password"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <Eye className="h-4 w-4 text-muted-foreground" />
                        )}
                      </Button>
                    </div>
                    {errors.password && (
                      <p className="text-sm text-destructive">{errors.password}</p>
                    )}
                  </div>

                  {/* Forgot Password Link */}
                  <div className="flex justify-end">
                    <Link to="/forgot-password">
                      <Button variant="link" className="h-auto px-0 text-sm" type="button">
                        Forgot password?
                      </Button>
                    </Link>
                  </div>
                </>
              )}
            </CardContent>

            <CardFooter className="flex flex-col gap-4">
              <Button 
                type="submit" 
                className="w-full" 
                size="lg"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {pendingMfaChallenge ? 'Verifying...' : 'Signing in...'}
                  </>
                ) : (
                  pendingMfaChallenge ? 'Verify and Sign in' : 'Sign in'
                )}
              </Button>
              {pendingMfaChallenge && (
                <Button
                  type="button"
                  variant="ghost"
                  className="w-full"
                  onClick={() => {
                    clearMfaChallenge();
                    setMfaCode('');
                    setBackupCode('');
                    setUseBackupCode(false);
                    setLoginError(null);
                  }}
                >
                  Back to credentials
                </Button>
              )}
              
            </CardFooter>
          </form>
        </Card>

        {/* Footer */}
        <p className="text-center text-sm text-muted-foreground mt-6">
          © {new Date().getFullYear()} CoreDent PMS. All rights reserved.
        </p>
      </div>
    </div>
  );
}
