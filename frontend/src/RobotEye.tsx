// src/RobotEye.tsx
import React from 'react';

const RobotEye = () => {
  return (
    <div className="flex items-center justify-center w-screen h-screen bg-gray-900">
      <div className="relative w-48 h-48 bg-white border-8 border-gray-600 rounded-full overflow-hidden">
        <div className="absolute w-24 h-24 bg-black rounded-full top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 animate-blink">
          <div className="absolute w-12 h-12 bg-blue-500 rounded-full top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"></div>
        </div>
      </div>
    </div>
  );
}

export default RobotEye;
