import java.util.Scanner;
class operator
{
 public static void main(String args[])
 {
 Scanner reader=new Scanner(System.in);
 System.out.print("Enter first number:");
 int a=reader.nextInt();
 System.out.print("Enter second number:");
 int b=reader.nextInt();
 System.out.println("ARITHMETIC OPERATOR:");
 System.out.println("Addition="+(a+b));
 System.out.println("Subraction="+(a-b));
 System.out.println("Multiplication="+(a*b));
 System.out.println("Division="+(a/b));
 System.out.println("Modulus="+(a%b));
 System.out.println("Increment="+(a++));
 System.out.println("Decrement="+(a--));
 }
}