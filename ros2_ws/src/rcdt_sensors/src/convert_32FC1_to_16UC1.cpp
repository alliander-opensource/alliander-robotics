// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "convert_32FC1_to_16UC1.hpp"

Convert32FC1to16UC1::Convert32FC1to16UC1() : Node("convert_32FC1_to_16UC1") {
  std::string ns = this->get_namespace();
  subscription = this->create_subscription<Image>(
      ns + "/depth/image_rect_raw_float", 10,
      std::bind(&Convert32FC1to16UC1::subscription_callback, this, _1));
  publisher = this->create_publisher<Image>(ns + "/depth/image_rect_raw", 10);
};

void Convert32FC1to16UC1::subscription_callback(Image msg) {
  auto input_image = cv_bridge::toCvCopy(msg);
  auto output_image = cv_bridge::CvImage();

  input_image->image *= 1000;  // m to mm
  input_image->image.convertTo(output_image.image, CV_16UC1);

  output_image.header = input_image->header;
  output_image.encoding = "16UC1";
  publisher->publish(*output_image.toImageMsg());
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Convert32FC1to16UC1>());
  rclcpp::shutdown();
}
