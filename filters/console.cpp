#include <sstream>
#include <iostream>
#include "console.hpp"

namespace findbug
{

	void print_txt (char *mess)
	{
		std::cout << mess << std::endl;
	}

	void print_int (int val)
	{
		//std::string mess = std::to_string(val);	// available in standard library since C++11
		std::stringstream ss;
		ss << val;
		std::string mess = ss.str();
		std::cout << mess << std::endl;
	}

}
