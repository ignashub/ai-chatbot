"use client";

import { useState } from 'react';
import axios from 'axios';
import { InputText } from 'primereact/inputtext';
import { Button } from 'primereact/button';
import { Card } from 'primereact/card';
import { Dropdown } from 'primereact/dropdown';
import { InputNumber } from 'primereact/inputnumber';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Tooltip } from 'primereact/tooltip';

interface NutritionResult {
  success: boolean;
  food_item?: string;
  quantity?: number;
  unit?: string;
  nutrition?: {
    calories: number;
    protein: number;
    carbs: number;
    fat: number;
    fiber: number;
    sugar: number;
  };
  message?: string;
}

const NutritionSearch = () => {
  const [foodItem, setFoodItem] = useState('');
  const [quantity, setQuantity] = useState<number>(100);
  const [unit, setUnit] = useState('g');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<NutritionResult | null>(null);

  const unitOptions = [
    { label: 'Grams (g)', value: 'g' },
    { label: 'Ounces (oz)', value: 'oz' },
    { label: 'Cup', value: 'cup' },
    { label: 'Tablespoon', value: 'tbsp' },
    { label: 'Teaspoon', value: 'tsp' },
    { label: 'Serving', value: 'serving' }
  ];

  const searchNutrition = async () => {
    if (!foodItem) return;

    setLoading(true);
    setResult(null);

    try {
      const response = await axios.post('/api/nutrition', {
        food_item: foodItem,
        quantity,
        unit
      });
      
      setResult(response.data);
    } catch (error) {
      console.error('Error searching nutrition:', error);
      setResult({
        success: false,
        message: 'Failed to retrieve nutrition information. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  const cardTitle = (
    <div className="flex items-center gap-2">
      <span>Nutrition Search</span>
      <i 
        className="pi pi-info-circle cursor-pointer nutrition-tooltip" 
        data-pr-tooltip="You can ask above the AI: 'What's the nutritional value of an apple?' or 'How many calories are in 200g of chicken breast?'"
        data-pr-position="right"
        data-pr-at="right+5 top"
        style={{ fontSize: '0.9rem' }}
      />
    </div>
  );

  return (
    <Card title={cardTitle} className="shadow-lg mb-4">
      <Tooltip target=".nutrition-tooltip, .food-item-tooltip, .quantity-tooltip, .unit-tooltip" />
      <div className="flex flex-col gap-3 mb-4">
        <div>
          <label htmlFor="foodItem" className="block mb-1">
            Food Item
            <i 
              className="pi pi-info-circle cursor-pointer ml-2 food-item-tooltip" 
              data-pr-tooltip="Enter a food name like 'apple', 'chicken breast', 'salmon', 'broccoli', 'rice', or 'egg'. Our database contains nutrition information for common foods."
              data-pr-position="right"
              style={{ fontSize: '0.9rem' }}
            />
          </label>
          <InputText
            id="foodItem"
            value={foodItem}
            onChange={(e) => setFoodItem(e.target.value)}
            placeholder="Enter a food item (e.g., apple, chicken breast)"
            className="w-full"
          />
        </div>
        
        <div className="flex gap-3">
          <div className="flex-1">
            <label htmlFor="quantity" className="block mb-1">
              Quantity
              <i 
                className="pi pi-info-circle cursor-pointer ml-2 quantity-tooltip" 
                data-pr-tooltip="Enter the amount of food you want nutrition information for. Default is 100."
                data-pr-position="top"
                style={{ fontSize: '0.9rem' }}
              />
            </label>
            <InputNumber
              id="quantity"
              value={quantity}
              onValueChange={(e) => setQuantity(e.value || 100)}
              min={0}
              className="w-full"
            />
          </div>
          
          <div className="flex-1">
            <label htmlFor="unit" className="block mb-1">
              Unit
              <i 
                className="pi pi-info-circle cursor-pointer ml-2 unit-tooltip" 
                data-pr-tooltip="Select the unit of measurement. Options include grams (g), ounces (oz), cups, tablespoons (tbsp), teaspoons (tsp), or servings."
                data-pr-position="top"
                style={{ fontSize: '0.9rem' }}
              />
            </label>
            <Dropdown
              id="unit"
              value={unit}
              options={unitOptions}
              onChange={(e) => setUnit(e.value)}
              className="w-full"
            />
          </div>
        </div>
        
        <Button
          label="Search"
          icon="pi pi-search"
          onClick={searchNutrition}
          disabled={loading || !foodItem}
          className="mt-2"
        />
      </div>
      
      {loading && (
        <div className="flex justify-center my-4">
          <ProgressSpinner style={{ width: '50px', height: '50px' }} />
        </div>
      )}
      
      {result && (
        <div className="mt-4">
          {result.success ? (
            <div className="p-4 border rounded bg-gray-50">
              <h3 className="text-xl font-bold mb-2">{result.food_item} ({result.quantity} {result.unit})</h3>
              
              <div className="grid grid-cols-2 gap-2">
                <div className="p-2 bg-blue-50 rounded">
                  <span className="font-bold">Calories:</span> {result.nutrition?.calories}
                </div>
                <div className="p-2 bg-green-50 rounded">
                  <span className="font-bold">Protein:</span> {result.nutrition?.protein}g
                </div>
                <div className="p-2 bg-yellow-50 rounded">
                  <span className="font-bold">Carbs:</span> {result.nutrition?.carbs}g
                </div>
                <div className="p-2 bg-red-50 rounded">
                  <span className="font-bold">Fat:</span> {result.nutrition?.fat}g
                </div>
                <div className="p-2 bg-purple-50 rounded">
                  <span className="font-bold">Fiber:</span> {result.nutrition?.fiber}g
                </div>
                <div className="p-2 bg-pink-50 rounded">
                  <span className="font-bold">Sugar:</span> {result.nutrition?.sugar}g
                </div>
              </div>
            </div>
          ) : (
            <div className="p-4 border rounded bg-red-50 text-red-700">
              {result.message}
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

export default NutritionSearch; 