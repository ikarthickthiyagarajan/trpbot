import React from 'react';
// @ts-ignore
import logo from '../../assets/srm_trp_logo.png';

const Header: React.FC = () => {
  return (
    <header>
      <img src={logo} alt="SRM TRP Engineering College Logo" />
      <h1>SRM TRP Engineering College Assistant</h1>
    </header>
  );
};

export default Header;