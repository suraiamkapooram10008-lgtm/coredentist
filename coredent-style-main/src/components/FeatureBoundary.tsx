// ============================================
// CoreDent PMS - Feature-Level Error Boundary
// Isolates failures to specific modules/features
// ============================================

import React, { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertCircle, RefreshCcw, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { logger } from '@/lib/logger';

interface FeatureBoundaryProps {
  children: ReactNode;
  featureName: string;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface FeatureBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class FeatureBoundary extends Component<FeatureBoundaryProps, FeatureBoundaryState> {
  constructor(props: FeatureBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<FeatureBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log with feature context using centralized logger
    logger.error(`Feature Error: ${this.props.featureName}`, error, {
      componentStack: errorInfo.componentStack,
      feature: this.props.featureName,
    });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="p-6 h-full flex items-center justify-center animate-in fade-in zoom-in duration-300">
          <Card className="max-w-md border-destructive/20 shadow-lg overflow-hidden">
            <div className="h-2 bg-destructive" />
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <div className="h-10 w-10 rounded-full bg-destructive/10 flex items-center justify-center">
                  <AlertCircle className="h-6 w-6 text-destructive" />
                </div>
                <CardTitle className="text-xl">Feature Unavailable</CardTitle>
              </div>
              <CardDescription>
                We encountered an issue while loading the <strong>{this.props.featureName}</strong> module. 
                Other parts of the system are still functioning normally.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {import.meta.env.DEV && (
                <div className="bg-muted p-3 rounded text-xs font-mono text-destructive overflow-auto max-h-32 mb-4">
                  {this.state.error?.message}
                </div>
              )}
              <p className="text-sm text-muted-foreground">
                You can try to reload this specific feature, or return to the dashboard.
              </p>
            </CardContent>
            <CardFooter className="flex gap-3 pt-2">
              <Button 
                variant="default" 
                onClick={this.handleReset}
                className="flex-1 gap-2"
              >
                <RefreshCcw className="h-4 w-4" />
                Reload Feature
              </Button>
              <Button 
                variant="outline" 
                onClick={() => window.location.href = '/dashboard'}
                className="flex-1 gap-2"
              >
                <Home className="h-4 w-4" />
                Dashboard
              </Button>
            </CardFooter>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
