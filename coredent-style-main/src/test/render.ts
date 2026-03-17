import { ReactElement } from 'react';
import { render, RenderOptions, screen, userEvent } from '@testing-library/react';
import { AllTheProviders } from './render.tsx';

const customRender = (ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) =>
  render(ui, { wrapper: AllTheProviders, ...options });

export { customRender as render, screen, userEvent };
