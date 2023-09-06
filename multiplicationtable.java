import java.util.Scanner;
class multiplication
{
 public static void main(String args[])
{
 Scanner reader=new Scanner(System.in);
 System.out.print("Enter a number:");
 int n=reader.nextInt();
  for(int i=1;i<=10;i++)
{
 System.out.println(n+"*"+i+"="+n*i);
}
}
} 