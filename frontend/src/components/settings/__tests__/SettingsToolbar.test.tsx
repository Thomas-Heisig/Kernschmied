import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import SettingsToolbar from '../SettingsToolbar';

test('SettingsToolbar calls handlers', () => {
  const onSave = jest.fn();
  const onReload = jest.fn();
  const onReset = jest.fn();

  const { getByText } = render(
    <SettingsToolbar isDirty={true} isSaving={false} onSave={onSave} onReload={onReload} onReset={onReset} />,
  );

  fireEvent.click(getByText('Neu laden'));
  fireEvent.click(getByText('Zurücksetzen'));
  fireEvent.click(getByText('Speichern'));

  expect(onReload).toHaveBeenCalled();
  expect(onReset).toHaveBeenCalled();
  expect(onSave).toHaveBeenCalled();
});
